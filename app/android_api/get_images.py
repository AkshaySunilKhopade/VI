import json
import os
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_andriod import *
from logger import logger
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, Counter
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user


def image_tostring(image_path):
    try:
        if image_path:
            # Clean path separators and remove leading 'IMAGES/' if duplicated
            image_path = image_path.strip().replace("\\", "/")
            if image_path.lower().startswith("images/"):
                image_path = image_path[7:]  # Remove 'IMAGES/' prefix

            full_path = os.path.normpath(os.path.join(BASE_IMAGE_DIR, image_path))

            if os.path.exists(full_path):
                with open(full_path, "rb") as img_file:
                    logger.info(f"Using full image path: {full_path}")
                    return base64.b64encode(img_file.read()).decode('utf-8')
            else:
                logger.error(f"Image not found at path: {full_path}")

    except Exception as eobj:
        logger.error(f"Exception occured in image_tostring method as : {eobj}")
    return None


def encode_images_to_base64(records):
    for record in records:
        image_path = record.get("image_path")
        encoded_image = image_tostring(image_path)  # Use helper to get base64

        if encoded_image:
            record["image"] = encoded_image
        else:
            record["image"] = None

        record.pop("image_path", None)  # Remove raw path for security and clarity

    return records




router = APIRouter()
@router.post("/native/get_images/")
async def get_images(request: Request,
    current_user: dict = Depends(get_current_user)) :

    try :
        body = await request.json()
        registration_no = body.get("registration_no")
        user_id = current_user["user_id"]

        if registration_no:
            logger.info(f"Regstration Number Get images : {registration_no}")
        else :
            logger.error(f"Registration no is required")
            return {"success" : False,"message" : "Registration No is required"}

        vechile = fetch_vehicle(registration_no)
        if not vechile:
            logger.error(f"Vechile not find for this registration no : {registration_no}")
            return {"success" : False,"message" : "vechile is not present for registration no"}
        
        vehicle_id = vechile["id"]
        records = get_part_images(user_id,vehicle_id)
        
        if not records:
            # here it returns if the user is differnet
            return {"success" : True, "message" : "Vehicle is already inspected by the other user"}
        
        result_json = encode_images_to_base64(records)

        return {"success" : True,"vechile" : result_json}

    except Exception as eobj:
        logger.error(f"Exception ouccurred in get_images as : {eobj}")