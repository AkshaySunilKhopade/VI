import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_web import *
from logger import logger
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from auth.auth import get_current_user


router = APIRouter()


#Dashboard Details
@router.post("/dashboard/")
async def dashboard(request: Request,current_user: dict = Depends(get_current_user)):
    try :

        body = await request.json()
        registration_no = body.get("registration_no")
        # print(current_user["user_id"])
        logger.info(f"In Dashboard Api Registartion no is  : {registration_no}")

        if not registration_no or registration_no.strip() == "":
            print("HIII")
            logger.error(f"Error in logger api as : Registration no is empty or null")
            return {"success" : False,"message" : "Registration No should be valid and Not Empty"}

        user_id = current_user["user_id"]
        vehicle = fetch_details_dashboard(registration_no,user_id)


        if vehicle == False:
            logger.error(f"Vehicle is already Inspected by the user")
            return {"success" : False,"message" : f"Vehicle is already Inspected by the other user"}
        
        elif not vehicle:
            return {"success": False, "message": f"No vehicle found with registration_no {registration_no}"}

        full_name = current_user['first_name'] + " " + current_user['last_name']
        logger.info(f"Success from dashbaord api")
        return {"success": True,"username" : full_name ,"vehicle_details": vehicle}
    
    except Exception as eobj:
        logger.error(f"Errro ocurred in dashboard api as : {eobj}")
        return {"success" : False,"message" : f"Exception ouccured in Dashboard api as : {eobj}"}