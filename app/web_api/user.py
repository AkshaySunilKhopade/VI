import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_web import *
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, Counter
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user
from logger import *


router = APIRouter()


@router.post("/create_user/")
async def create_user_endpoint(username: str = Form(...),mobile_no: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and password are required")
    user_created = create_user(username,mobile_no, password)
    if not user_created:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    return {"success": True, "message": "User created successfully"}

# Login to get JWT token
@router.post("/token/")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try :
        mobile_no = form_data.username  # Treat this as mobile number
        password = form_data.password

        user = authenticate_user(mobile_no, password)  # Your function that fetches user by mobile_no and verifies password
        
        if not user:
            logger.error(f"User Not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect mobile number or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user["mobile_no"]})

        if not access_token:
            logger.error(f"Access Token not created for user : {user['mobile_no']}")
            return {"success": False,"message" : f"Access Token not created for user : {user['mobile_no']}"}

        logger.info(f"User Logged in Suuccessfully : {user['username']}")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as eobj :
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect mobile number or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # return {"success" : False, "message" : f""}

@router.post("/logout")
def logout(response: Response):
    # Remove the JWT token by deleting the cookie on the client
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


#user details api 
@router.post("/user_detials/")
def user_data(request: Request,current_user: dict = Depends(get_current_user)):
    try :
        user_id = current_user["user_id"]
        user = user_details(user_id)
        print("USer : ",user)
        if not user:
            raise ValueError("User not found")
    
        return {"success" : True,"User_detials" : user}

    except Exception as eobj :
        logger.error(f"Exception occured in User Detials api : {eobj}")
        return {"success" : False,"messgae" : "Unbale to get the user data"}