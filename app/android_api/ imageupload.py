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


@router.post("/native/upload_image/")
async def upload_image(
    registration_no: str = Form(...),
    part_name: str = Form(...),  # Single part name (key)
    file: UploadFile = File(...),  # Single image file
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["user_id"]
        logger.info(f"Single image upload: {registration_no} - {part_name}")
        images = {}
        
        
        
        # Special handling for suppressor_cap and suppressor_devices
        if part_name in ["suppressor_cap", "suppressor_devices"]:
            logger.info(f"Special handling for {part_name} - bypassing model classification")
            
            image_bytes = await file.read()
            ext = os.path.splitext(file.filename)[1]
            new_filename = f"{part_name}_{registration_no}_1{ext}"
            save_path = os.path.join(IMAGES_DIR, new_filename)
            
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            
            status = True
            images[part_name] = [status]
            
            # Store in database with status=True
            record = check_imageupload(registration_no,part_name)
            
            insert_vehicle_image(registration_no, user_id, new_filename, part_name, status)
            logger.info(f"Stored {part_name} image with status=True (no classification)")
            
            return {
                "success": True,
                "registration_no": registration_no,
                "received_images": [{part_name: [status]}]
            }
        
        # Normal processing for other parts
        image_bytes = await file.read()
        np_image = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        
        logger.info(f"CAlling the imager classifier model for : {part_name} and {registration_no}")
        parts_type = vimodel_image_classifier(image)
        logger.info(f"Predicted part type: {parts_type}")
        
        ext = os.path.splitext(file.filename)[1]
        new_filename = f"{part_name}_{registration_no}_1{ext}"
        save_path = os.path.join(IMAGES_DIR, new_filename)
        
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        
        # Determine status based on prediction match
        if part_name == parts_type["label"]:
            status = True
        else:
            status = False
        
        images[part_name] = [status]
        
        insert_vehicle_image(registration_no, user_id, new_filename, part_name, status)
        
        logger.info(f"Inspection result for {part_name}: {status}")
        return {
            "success": True,
            "registration_no": registration_no,
            "received_images": [{part_name: [status]}]
        }
        
    except Exception as eobj:
        logger.error(f"Upload Image API failed, error: {eobj}")
        return {"success": False, "message": f"Exception occurred: {eobj}"}
