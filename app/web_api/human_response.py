import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_web import *
from logger import logger
from typing import List
from fastapi import FastAPI, Depends,Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user

router = APIRouter()

#Human Response gets writtern here
@router.post("/human_response/")
async def human_response(request: Request,current_user: dict = Depends(get_current_user)):
    try : 
        body = await request.json()
        registration_no = body["registration_no"]

        if not registration_no or registration_no.strip() == "":
            print("HIII")
            logger.error(f"Error in human_response api as : Registration no is empty or null")
            return {"success" : False,"message" : "Registration No should be valid and Not Empty"}

        if not registration_no:
            logger.error(f"Error in human_response api as : Registration no is empty or null")
            return {"success": False, "message": "registration_no is required"}
        
        main_part = body["detections"][0]["part"]    
        human_verdict = body["detections"][0]["human_response"]
        part_name = body["detections"][0]["part"]
        status = body["detections"][0]["status"]
        main_ai_aggregate_verdict = body["detections"][0]["ai_verdict"]
        main_aggregate_confidence = body["detections"][0]["confidence_score"]
        main_defect = body["detections"][0]["defect"]
        main_confidence_score = body["detections"][0]["confidence_score"]
        main_image_count = len(body["detections"][0]["images_path"])
        human_status = body["detections"][0]['human_status']
        user_id = current_user['user_id']

        data = {
            "main_part" : body["detections"][0]["part"],    
            "human_verdict" : body["detections"][0]["human_response"],
            "part_name" : body["detections"][0]["part"],
            "status" : body["detections"][0]["status"],
            "main_ai_aggregate_verdict" : body["detections"][0]["ai_verdict"],
            "main_aggregate_confidence" : body["detections"][0]["confidence_score"],
            "main_defect" : body["detections"][0]["defect"],
            "main_confidence_score" : body["detections"][0]["confidence_score"],
            "main_image_count" : len(body["detections"][0]["images_path"]),
            "human_status" : body["detections"][0]['human_status'],
            "user_id" : current_user['user_id'],
        }

        print("Human REsponse json : ",data)

        print("Reistration Number : ",registration_no)
        
        
        print("Human Response : ",human_verdict)
        full_name = current_user['first_name'] + " " + current_user['last_name']

        insert_vehicle_part_verdicts(registration_no, main_part, main_ai_aggregate_verdict, main_aggregate_confidence,main_image_count,status,main_defect,main_confidence_score)
        vehicle_mapping(user_id,registration_no,main_part)
        update_human_response(registration_no,human_verdict,part_name,human_status)
        
        # refresh_json = final_json
        logger.info(f"Success from human_response api")

        return {"success":True,"username" : full_name,"message": "Human verdict updated"}
    
    except Exception as eobj : 
        logger.error(f"Error in human_response api as : Registration no is empty or null")
        return {"success" : False,"message" : f"Error occurred in Human Resposnsse api as : {eobj}"}
    

