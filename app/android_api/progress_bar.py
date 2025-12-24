import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_andriod import *
from logger import logger
from utils.load_llm import map_label_with_llm
from utils.load_imgClassifier import image_classifier
from utils.mirror_imgClassifier import mirror_image_classifier
from utils.rear_imgClassifier import rearlight_image_classifier
from utils.load_headlamp import headlamp_image_classifier
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, Counter
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user

router = APIRouter()

@router.post("/native/progress_bar/")
async def progress_bar(request: Request,current_user: dict = Depends(get_current_user)):
    body = await request.json()
    registration_no = body.get("registration_no")
    user_id_body = body.get("user_id")
    print(user_id_body)
    # print(current_user["user_id"])

    # if not registration_no or registration_no.strip() == "":
    #     print("HIII")
    #     return {"success" : False,"message" : "Registration No should be valid and Not Empty"}

    # if not registration_no:
    #     return {"success": False, "message": "registration_no is required"}
    try : 
        user_id = ""
        if not user_id_body:
            user_id = current_user["user_id"]
        else:
            user_id = user_id_body
        
        print("User id in PGB : ",user_id)
        vehicle = progress_bar_mapping(registration_no,user_id)
        vechicle_detials = fetch_vehicle(registration_no)
        
        # print(vechicle_detials[0]['owner_name'])

        owner_name = vechicle_detials['owner_name']
        full_name = current_user['first_name'] + " " + current_user['last_name']

        # print(vechicle_detials)

        if not vehicle:
            logger.error(f"no vechile found for the user id : {current_user['user_id']}")
            return {"success": False, "message": f"No Data found the {current_user["user_id"]}"}
        
        logger.info(f"Progress Bar Sent")
        return {"success": True,"registration_no":registration_no,"username":full_name, "owner_name":owner_name, "vehicle_details": vehicle,}
    
    except Exception as eobj : 
        logger.error(f"Exception occured in progress_bar api as : {eobj}")
        return {"success" : False,"message" : f"Exception occured in progress_bar api as : {eobj}"}