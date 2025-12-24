import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_andriod import *
from logger import logger
from utils.parts_classifier import vimodel_image_classifier
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user
from starlette.datastructures import UploadFile  # Import from starlette as per your runtime
    
IMAGES_DIR = "IMAGES"
BASE_IMAGE_DIR = r"./IMAGES"  # Change to your actual IMAGES folder path
router = APIRouter()


#uploads image here 
@router.post("/native/upload_image/")
async def upload_image(request: Request,
    current_user: dict = Depends(get_current_user)):
    try:
        form = await request.form()
        print(form)
        registration_no = None
        images = {}
        user_id = current_user["user_id"]
        # Extract registration_no if present
        if "registration_no" in form:
            registration_no = form.get("registration_no")
            logger.info(f"Registration Number: {registration_no}")
        status = ""
        for key in form.keys():
            logger.info(f"key are :{key}")
            if key == "registration_no":
                logger.info("Skipped the registrtation key")
                continue
            # Special handling for suppressor_cap and suppressor_devices
            # These keys bypass model classification and are stored with status=True
            if key in ["suppressor_cap", "suppressor_devices"]:
                logger.info(f"Special handling for {key} - bypassing model classification")
                
                files = form.getlist(key)
                if not files:
                    continue
                count = 1
                for file in files:
                    if isinstance(file, UploadFile):
                        image_bytes = await file.read()
                        
                        ext = os.path.splitext(file.filename)[1]
                        new_filename = f"{key}_{registration_no}_{count}{ext}"
                        save_path = os.path.join(IMAGES_DIR, new_filename)
                        with open(save_path, "wb") as f:
                            f.write(image_bytes)
                        if key not in images:
                            images[key] = []
                        
                        # Directly set status to True for these special keys
                        status = True
                        images[key].append(status)
                        
                        # Store in database with status=True
                        insert_vehicle_image(registration_no, user_id, new_filename, key, status)
                        logger.info(f"Stored {key} image with status=True (no classification)")
                        count += 1
                
                continue  # Skip to next key
            # Normal processing for all other keys
            files = form.getlist(key)  # list of UploadFile under this key
            if not files:
                continue
            count = 1
            for file in files:
                if isinstance(file, UploadFile):
                    image_bytes = await file.read()
                    np_image = np.frombuffer(image_bytes, np.uint8)
                    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
                    parts_type = vimodel_image_classifier(image)
                    logger.info(f"Predicted part type: {parts_type}")
                    ext = os.path.splitext(file.filename)[1]
                    print(count)
                    new_filename = f"{key}_{registration_no}_{count}{ext}"
                    save_path = os.path.join(IMAGES_DIR, new_filename)
                    with open(save_path, "wb") as f:
                        f.write(image_bytes)
                    if key not in images:
                        images[key] = []
                        
                    if key == parts_type["label"]:
                        status = True
                        images[key].append(status)
                        #here will code the classifiers for ai detection in phase 2
                        # insert_vehicle_image(registration_no, user_id, new_filename, key, True)                
                    else :
                        status = False
                        images[key].append(status)
                        
                    insert_vehicle_image(registration_no, user_id, new_filename, key, status)                
                    count += 1
        logger.info(f"Inspection results for parts: {images}")
        received_images_list = [{k: v} for k, v in images.items()]
        return {
            "success": True,
            "registration_no": registration_no,
            "received_images": received_images_list
        }
    except Exception as eobj:
        logger.error(f"Upload Image API failed, error: {eobj}")
        return {"success": False, "message": f"Exception occurred: {eobj}"}