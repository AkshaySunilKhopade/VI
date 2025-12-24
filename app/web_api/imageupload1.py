import json
import os
import cv2
import numpy as np
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form,Request,Response,APIRouter
from db.db_web import *
from logger import logger
from utils.load_llm import map_label_with_llm
from utils.load_imgClassifier import image_classifier
from utils.mirror_imgClassifier import mirror_image_classifier
from utils.rear_imgClassifier import rearlight_image_classifier
from utils.load_headlamp import headlamp_image_classifier
from utils.windshield import windshield_image_classifier
from utils.load_foglamp_classifier import foglamp_image_classifier
from utils.load_tyreclassifier import tyre_image_classifier
from utils.load_wiperclassifier import wiper_image_classifier
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, Counter
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from auth.auth import authenticate_user, create_access_token, get_current_user, create_user

IMAGES_DIR = "IMAGES"
BASE_IMAGE_DIR = r"./IMAGES"  # Change to your actual IMAGES folder path
router = APIRouter()



def image_tostring(image_path):
    try :
        if image_path:
            # Clean and normalize path separators
            image_path = image_path.strip().replace("\\", "/") 
            # Remove duplicate "IMAGES/" prefix if present
            if image_path.lower().startswith("images/"):
                image_path = image_path[7:]  # remove 'IMAGES/' prefix
            
            # Combine with base directory for absolute path
            full_path = os.path.normpath(os.path.join(BASE_IMAGE_DIR, image_path))


            if os.path.exists(full_path):
                with open(full_path, "rb") as img_file:
                    logger.info(f"Using full image path: {full_path}")
                    return base64.b64encode(img_file.read()).decode('utf-8')
            else:
                logger.error(f"Image not found at path: {full_path}")
    
    except Exception as eobj :
            print("Empty image path")
            logger.error(f"Exception occured in image_tostring method as : {eobj}")
            return None


#here the final json is made 
def final_json(detection_list):
    try : 
        # Mapping dictionary for defect names
        defect_name_map = {
            # Windshield / Windscreen related
            "windscreen_tinted": "Windscreen Tinted",
            "windscreen_crack": "Windscreen Cracked",
            "good_windshield": "Windscreen Good",

            # Headlamp related
            "headlamp_crack": "Headlamp Cracked",
            "headlamp_faded": "Headlamp Faded",
            "headlamp_moisture": "Headlamp Moisture",
            "good_headlight": "Headlamp Good",

            # Rear light related
            "back_headlight_broken": "Rear Headlight Broken",
            "back_headlight_moisture": "Rear Headlight Moisture",
            "good_backlight": "Rear Headlight Good",

            # Mirror related
            "good_mirror": "Mirror Good",
            "mirror_broken": "Mirror Broken",
            "mirror_crack": "Mirror Cracked",

            # Fog lamp related (new)
            "fog_lamp_broken": "Fog Lamp Broken",
            "good_fog_lamp": "Fog Lamp Good",

            # "tyer_damage","good_tyer", "broken_wiper","good_wiper"
            "tyer_damage" : "Vehicle Tyre is Damaged",
            "good_tyer" : "Good Tyre",

            "broken_wiper" : "Windscreen Wiper is broken",
            "good_wiper" : "windscreen Wiper is good condition"
        }


        
        grouped = defaultdict(lambda: {
            "verdict_fail": False,
            "defects": [],
            "confiden_scores": [],
            "violated_rules": set(),
            "statuses": [],
            "images": set()
        })

        for det in detection_list:
            part = det['part']
            grouped[part]['defects'].append(det['defect'])
            grouped[part]['confiden_scores'].append(det.get('confiden_score', 0))
            if "not eligible" in det['ai_verdict'].lower():
                grouped[part]['verdict_fail'] = True
            if det.get('violated_rule') and det['violated_rule'] != "NA":
                grouped[part]['violated_rules'].add(det['violated_rule'])
            
            grouped[part]['statuses'].append(det.get('status', '').lower())
            grouped[part]['images'].add(det['images'])


        results = []
        for part, data in grouped.items():
            max_confidence_index = data['confiden_scores'].index(max(data['confiden_scores']))
            overall_defect_code = data['defects'][max_confidence_index]
            overall_defect = defect_name_map.get(overall_defect_code, overall_defect_code)  # map good name or fallback
            overall_confidence_score = max(data['confiden_scores']) if data['confiden_scores'] else 0
            status = data['statuses'][max_confidence_index]

            if status == 'fail':
                ai_verdict = f"The {part} shows a {overall_defect} defect, which is not eligible for insurance coverage according to the policy guidelines."
            else:
                ai_verdict = "Covered"

            # Map confidence score to confidence level
            if overall_confidence_score <= 0.3:
                confidence_level = "Minor"
            elif overall_confidence_score <= 0.6:
                confidence_level = "Moderate"
            else:
                confidence_level = "Major"

            if data['confiden_scores']:
                max_confidence_index = data['confiden_scores'].index(max(data['confiden_scores']))
                violated_rule = next(iter([det['violated_rule'] for det in detection_list if det['part'] == part][max_confidence_index: max_confidence_index+1]), "NA")
            else:
                violated_rule = "NA"

            combined_image_paths = list(data['images'])
            images_base64 = [image_tostring(img) for img in combined_image_paths]
            images_path = list(data['images'])

            results.append({
                "part": part,
                "defect": overall_defect,
                "confidence": confidence_level,
                "confidence_score": overall_confidence_score,
                "violated_rule": violated_rule,
                "ai_verdict": ai_verdict,
                "human_response": None,
                "human_status" : None,
                "status": status,
                "images_path" :images_path,
                "images": images_base64,
            })

        return results
    except Exception as eobj :
        logger.error(f"Exception occured in final_json method as : {eobj}")


#uploads image here 
@router.post("/upload_image/") 
async def upload_image(
    registration_no: str = Form(...),
    files: list[UploadFile] = File(...),
    parts: str = Form(...),
    current_user: dict = Depends(get_current_user)
    ):

    try : 

        if not registration_no or registration_no.strip() == "":
            print("HIII")
            logger.error("Registration No should be valid and Not Empty")
            return {"success" : False,"message" : "Registration No should be valid and Not Empty"}

        if not registration_no:
            logger.error("Registration No should be valid and Not Empty")
            return {"success": False, "message": "registration_no is required"}

        if len(files) == 0:
            logger.error("At least one image file must be uploaded")
            return {"success": False, "message": "At least one image file must be uploaded"}


        vehicle = fetch_vehicle(registration_no)
        if not vehicle:
            logger.error(f"Vehicle with registration_no {registration_no} not found")
            return {"success": False, "message": f"Vehicle with registration_no {registration_no} not found"}


        detections = []
        # print(files)
        count = 1

        for file in files:    
            image_bytes = await file.read()
            try:
                np_image = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
                if image is None:
                    detections.append({"filename": file.filename, "error": "Invalid image"})
                    continue
                
                # AI classifier
                logger.info("Calling image classifier.")
                #remove if else convert to dict
                if parts == "Mirrors": 
                    part_type = mirror_image_classifier(image)
                elif parts == "Rear_Backlight" : 
                    part_type = rearlight_image_classifier(image)
                elif parts == "HeadLamp":
                    part_type = headlamp_image_classifier(image)
                elif parts == "Windshield":
                    part_type = windshield_image_classifier(image)
                elif parts == "Foglamp":
                    part_type = foglamp_image_classifier(image)
                elif parts == "Wiper": 
                    part_type = wiper_image_classifier(image)
                elif parts == "Tyre":
                    part_type = tyre_image_classifier(image)
                else : 
                    raise Exception("Please a part name") 


                print("Part_type",part_type)
                
                label = part_type["label"].lower()

                if label in ("headlamp_moisture", "headlamp_faded", "headlamp_crack", "good_headlight"):
                    part = "Head Lamp"
                elif label in ("good_mirror", "mirror_broken", "mirror_crack"):
                    part = "Mirror"
                elif label in ("back_headlight_broken", "back_headlight_moisture", "good_backlight"):
                    part = "Back Light"
                elif label in ("good_windshield", "windscreen_crack", "windscreen_tinted"):
                    part = "Windshield"
                elif label in ("fog_lamp_broken", "good_fog_lamp"):
                    part = "Fog Lamp"
                elif label in ("broken_wiper","good_wiper") : 
                    part = "Wiper"
                elif label in ("tyer_damage","good_tyer"):
                    part = "Tyre"
                else:
                    part = "Unknown"

                
                # part_type = image_classifier(image)

                # part = "Head Lamp" if part_type["label"].lower() in (
                #     "headlamp_moisture", "headlamp_faded", "headlamp_crack"
                # ) else "Windsheild"

                ext = os.path.splitext(file.filename)[1]
                print(count)
                new_filename = f"{parts}_{registration_no}_{count}{ext}"
                save_path = os.path.join(IMAGES_DIR, new_filename)
                with open(save_path, "wb") as f:
                    f.write(image_bytes)
                

                # label = part_type['label'].strip().lower()
                confidence_val = part_type["confidence"]

                prediction = map_label_with_llm(label)
                print("Prediction from the llm  : ",prediction)

                if prediction['status'] == "fail":
                    verdict = "This circumstance is not eligible for insurance coverage according to the policy guidelines."
                else:
                    verdict = "Covered"
                violated_rule = prediction.get('violated_rule', "NA")

                if confidence_val <= 0.3:
                    confidence_status = "Minor"
                elif confidence_val <= 0.6:
                    confidence_status = "Moderate"
                else:
                    confidence_status = "Major"

                print(part)

                info = {
                    "part": part,
                    "defect": label,
                    "confidence": confidence_status,
                    "confiden_score" : confidence_val,
                    "violated_rule": violated_rule,
                    "ai_verdict": verdict,
                    "human_response": None,
                    "human_status" : None,
                    "status" : prediction["status"],
                    "image_path" : save_path,
                    "images" : save_path,
                }

                #this fucntion call is used to save the image path and its data
                insert_vehicle_image(registration_no, save_path,info["ai_verdict"],info["part"],info["defect"],info["confidence"])  
                detections.append(info)
                count = count + 1


            except Exception as e:
                logger.error(f"Error processing image {file.filename}: {e}")
                detections.append({"filename": file.filename, "error": str(e)})
        
        #this fucntion returns the 1 final json for response
        main_json = final_json(detections)
        user_id = current_user["user_id"]
        
        #this data is for updating the final table
        main_part = main_json[0]["part"]
        main_ai_aggregate_verdict = main_json[0]["ai_verdict"]
        main_confidence_score = main_json[0]["confidence_score"]
        main_aggregate_confidence = main_json[0]["confidence"]
        main_status = main_json[0]["status"]
        main_defect = main_json[0]["defect"]
        main_image_count = len(main_json[0]["images"])

        full_name = current_user['first_name'] + " " + current_user['last_name']
        print(full_name)

        # insert_vehicle_part_verdicts(registration_no, main_part, main_ai_aggregate_verdict, main_aggregate_confidence,main_image_count,main_status,main_defect,main_confidence_score)
        # vehicle_mapping(user_id,registration_no,main_part)
        
        logger.info(f"Image Detctions are done for registration no : {registration_no} and user : {current_user['username']}")
        return {"success": True, "username" : full_name, "detections": main_json}
        # return {"success": True, "detections": detections}

    except Exception as eobj :
        logger.error(f"Upload Image api fialed, error occured as : {eobj}")
        return {"success" : False,"message" : f"Exception occured in uploading image as : {eobj}"}
    

