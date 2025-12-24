import json
import os
import cv2
import numpy as np
import base64
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response, APIRouter, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from collections import defaultdict, Counter
from db.db_andriod import *
from logger import logger
from utils.load_llm import map_label_with_llm
from utils.load_imgClassifier import image_classifier
from utils.mirror_imgClassifier import mirror_image_classifier
from utils.rear_imgClassifier import rearlight_image_classifier
from utils.load_headlamp import headlamp_image_classifier
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user

router = APIRouter()

@router.post("/native/human_status/")
async def human_status(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        body = await request.json()
        
        registration_no = body.get("registration_no")
        verdicts_array = body.get("verdicts", [])  # Array of verdict objects
        
        user_id = current_user["user_id"]

        if not registration_no:
            logger.error(f"Registration no is required")
            return {"success": False, "message": "Registration no is required"}
        
        logger.info(f"In human status api, Received the registration no: {registration_no}")

        if not verdicts_array or len(verdicts_array) == 0:
            logger.error(f"Verdicts array is empty or missing")
            return {"success": False, "message": "Verdicts array is required"}

        # Create base Image folder structure
        accepted_base_folder = "accepted"
        rejected_base_folder = "rejected"
        
        # Create base folders if they don't exist
        os.makedirs(accepted_base_folder, exist_ok=True)
        os.makedirs(rejected_base_folder, exist_ok=True)

        processed_count = 0
        
        # Process each verdict in the array
        for verdict_item in verdicts_array:
            part_name = verdict_item.get("part_name")
            is_reject = verdict_item.get("isReject", False)
            is_accept = verdict_item.get("isAccept", False)
            reason = verdict_item.get("reason", "")
            image = verdict_item.get("image", "")
            
            if not part_name:
                logger.warning(f"Skipping item with missing part_name")
                continue
            
            # Determine human verdict and status based on isReject/isAccept
            if is_reject:
                # If rejected, use the reason provided
                h_status = "Reject"
                human_verdict = reason if reason else "Rejected by human"
                logger.info(f"Rejecting part: {part_name} with reason: {human_verdict}")
                
                # Save image to rejected folder with part_name subfolder
                if image:
                    try:
                        # Create part-specific subfolder in rejected folder
                        part_rejected_folder = os.path.join(rejected_base_folder, part_name)
                        os.makedirs(part_rejected_folder, exist_ok=True)
                        
                        # Decode base64 image
                        image_data = base64.b64decode(image)
                        nparr = np.frombuffer(image_data, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        # Generate filename with timestamp to preserve original name pattern
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        image_filename = f"{part_name}_{timestamp}.jpg"
                        image_path = os.path.join(part_rejected_folder, image_filename)
                        cv2.imwrite(image_path, img)
                        logger.info(f"Saved rejected image to: {image_path}")
                    except Exception as img_error:
                        logger.error(f"Error saving rejected image for {part_name}: {img_error}")
                
                update_human_response(registration_no, part_name, h_status, human_verdict)
                vehicle_mapping(user_id, registration_no, part_name)
                processed_count += 1
                
            elif is_accept:
                # If accepted, set standard acceptance message
                h_status = "Accept"
                human_verdict = None
                logger.info(f"Accepting part: {part_name}")
                
                # Save image to accepted folder with part_name subfolder
                if image:
                    try:
                        # Create part-specific subfolder in accepted folder
                        part_accepted_folder = os.path.join(accepted_base_folder, part_name)
                        os.makedirs(part_accepted_folder, exist_ok=True)
                        
                        # Decode base64 image
                        image_data = base64.b64decode(image)
                        nparr = np.frombuffer(image_data, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        # Generate filename with timestamp to preserve original name pattern
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        image_filename = f"{part_name}_{timestamp}.jpg"
                        image_path = os.path.join(part_accepted_folder, image_filename)
                        cv2.imwrite(image_path, img)
                        logger.info(f"Saved accepted image to: {image_path}")
                    except Exception as img_error:
                        logger.error(f"Error saving accepted image for {part_name}: {img_error}")
                
                update_human_response(registration_no, part_name, h_status, human_verdict)
                vehicle_mapping(user_id, registration_no, part_name)
                processed_count += 1
            else:
                logger.warning(f"Item for part {part_name} has neither isReject nor isAccept set to true")

        logger.info(f"Processed {processed_count} verdicts for registration: {registration_no}")
        
        return {"success": True, 
                "message": f"Processed {processed_count} verdicts", 
                "registration_no": registration_no}
        
    except Exception as eobj:
        logger.error(f"Exception in Human status api as : {eobj}")
        return {"success": False, "message": f"Error processing request: {str(eobj)}"}


# insert_vehicle_part_verdicts(registration_no, main_part, main_ai_aggregate_verdict, main_aggregate_confidence,main_image_count,status,main_defect,main_confidence_score)
# vehicle_mapping(user_id,registration_no,main_part)
# update_human_response(registration_no,human_verdict,part_name,human_status)

                                                                             