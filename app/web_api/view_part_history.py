import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_web import *
from logger import logger
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, Counter
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user

router = APIRouter()

#Get vehicle details for saved part
@router.post("/history/")
async def view_history(request: Request,current_user: dict = Depends(get_current_user)):
    try :
        body = await request.json()
        registration_no = body.get("registration_no")
        part_name = body.get("part_name")

        if not registration_no or registration_no.strip() == "":
            print("HIII")
            logger.error(f"Error in history api as : Registration no is empty or null")
            return {"success" : False,"message" : "Registration No should be valid and Not Empty"}

        if not registration_no:
            logger.error(f"Error in history api as : Registration no is empty or null")
            return {"success": False, "message": "registration_no is required"}

        vehicle = view_histroy(registration_no,[part_name])
        full_name = current_user['first_name'] + " " + current_user['last_name']


        if not vehicle:
            logger.error(f"No vehicle found with registration_no {registration_no}")
            return {"success": False, "message": f"No vehicle found with registration_no {registration_no}"}
        
        logger.info("History Sent of vechicle")
        return {"success": True,"username" : full_name ,"vehicle_details": vehicle}
    

    except Exception as eobj : 
        return {"success": False, "message": f"No vehicle found with registration_no {registration_no}"}
