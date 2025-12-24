import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_andriod import *
from logger import logger
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user


router = APIRouter()



@router.post("/native/user_history/")    #here all the vehcile assositated to the user is shown
async def userhistory(request: Request,current_user: dict = Depends(get_current_user)):
    try : 
        # body = await request.json()
        user_id  = current_user["user_id"]
        vehicle = user_history(user_id)
        print(type(vehicle))

        json_response = json.dumps(vehicle, indent=2)
        print(type(vehicle))

        full_name = current_user['first_name'] + " " + current_user['last_name']

        if vehicle is None: 
            return {"success" : True,"username" : full_name,"message" : f"No vechile found for the user","vehicle_details" : []} 

        logger.info(f"User History Sent")
        return {"success": True, "username":full_name,"vehicle_details": vehicle}


    except Exception as eobj : 
        logger.error(f"error ouccured at user history api as : {eobj} ,for user : {current_user['user_id']}")
        return {"success" : False,"message" : f"Exception in User history as  : {eobj}"} 
