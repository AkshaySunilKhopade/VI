import json
import os
import cv2
import numpy as np
import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from logger import logger
from db.db_andriod import insert_vehicle_image
from auth.auth import get_current_user
from utils.parts_classifier import vimodel_image_classifier

IMAGES_DIR = "IMAGES"
router = APIRouter()


@router.post("/native/upload_image/")
async def upload_image(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple vehicle part images for classification.

    Expects a multipart/form-data request with:
    - registration_no: str
    - Any number of keys (e.g., front_bumper, rear_bumper), each with one or more images.

    Returns:
    - success: bool
    - registration_no: str
    - received_images: list of dicts mapping part key to list of booleans (status per image)
    """
    try:
        form = await request.form()
        user_id = current_user["user_id"]
        registration_no = form.get("registration_no")
        images = {}

        logger.info(f"Registration Number: {registration_no}")

        # Collect tasks for parallel inference
        inference_tasks = []
        inference_meta = []

        for key in form.keys():
            if key == "registration_no":
                continue

            files = form.getlist(key)
            if not files:
                continue

            count = 1
            for file in files:
                if not isinstance(file, UploadFile):
                    continue

                image_bytes = await file.read()
                np_image = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

                # Queue parallel model call
                inference_tasks.append(
                    run_in_threadpool(vimodel_image_classifier, image)
                )

                inference_meta.append({
                    "key": key,
                    "file": file,
                    "count": count,
                    "image_bytes": image_bytes
                })

                count += 1

        # Execute all inferences in parallel
        results = await asyncio.gather(*inference_tasks)

        # Process results (DB + file save)
        for meta, parts_type in zip(inference_meta, results):
            key = meta["key"]
            file = meta["file"]
            count = meta["count"]
            image_bytes = meta["image_bytes"]

            ext = os.path.splitext(file.filename)[1]
            new_filename = f"{key}_{registration_no}_{count}{ext}"
            save_path = os.path.join(IMAGES_DIR, new_filename)

            # Save image
            with open(save_path, "wb") as f:
                f.write(image_bytes)

            if key not in images:
                images[key] = []

            status = key == parts_type["label"]
            images[key].append(status)

            # DB insert
            insert_vehicle_image(
                registration_no,
                user_id,
                new_filename,
                key,
                status
            )

            logger.info(
                f"Image {new_filename} → "
                f"Predicted: {parts_type['label']} "
                f"(conf={parts_type['confidence']}) "
                f"Status={status}"
            )

        received_images_list = [{k: v} for k, v in images.items()]

        return {
            "success": True,
            "registration_no": registration_no,
            "received_images": received_images_list
        }

    except Exception as e:
        logger.error(f"Upload Image API failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }
