import base64
import json
import os
from typing import Set
import mysql.connector
from logger import *

# This is the connection function for
def get_connection():
    try:
        return mysql.connector.connect(
            host="172.20.1.216",         # MySQL host
            user="visual_inspection_user",              # MySQL username
            password="TbCdgLzp6-91",  # MySQL password
            database="visual_inspection_solution"   # Your database name
    )
    except mysql.connector.Error as e:
        raise Exception(f"Error connecting to database: {e}")

# def get_connection():
#     try :
#         return mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="root",
#             database="VI"
#         )
    
#     except mysql.connector.Error as e:
#         raise Exception(f"Error connecting to database: {e}")   



BASE_IMAGE_DIR = r"./IMAGES"  # Change to your actual IMAGES folder path

def image_path_to_base64(image_path):
    if image_path:
        # Remove surrounding spaces and replace backslashes with forward slashes
        image_path = image_path.strip().replace("\\", "/")
        # Remove "images/" prefix if present
        if image_path.lower().startswith("images/"):
            image_path = image_path[7:]

        full_path = os.path.join(BASE_IMAGE_DIR, image_path)
        print("Using full image path:", full_path)

        if os.path.exists(full_path):
            with open(full_path, "rb") as img_file:
                img_bytes = img_file.read()
                imagestring  = base64.b64encode(img_bytes).decode('utf-8')
                return imagestring
        else:
            print("Image not found at path:", full_path)
    else:
        print("Empty image path")
    return None


def user_details(user_id : str):
    try : 
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        print(user_id)
        cursor.execute(
            """
            SELECT user_id,username,first_name,last_name,email,created_at,mobile_no
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()
        if not user:
            logger.error(f"User not found for user user id : {user_id}")
            raise Exception(f"Unable to get the data of the user id : {user_id}")

        print("USer in db  : ",user)
        cursor.close()
        db.close()
        logger.info("User details send successfullly from db")
        return user
    except Exception as eobj:
        logger.error(f"Exception from : {eobj}")
        raise Exception(f"USer detials exception ouccured as  : {eobj}")

# This is general function fetching the vehicle from its registration_no
def fetch_vehicle(registration_no : str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM vehicles_new
            WHERE registration_no = %s
            """,
            (registration_no,)
        )
        vehicles = cursor.fetchone()
        cursor.close()
        db.close()
        return vehicles
    except Exception as e:
        raise Exception(f"Error in fetch_vehicle: {e}")



# Dashboard Details
def fetch_details_dashboard(registration_no: str,user_id : str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT chassis_no, registration_no, registration_date, engine_no, model, color,
                unloaded_weight, rc_status, vehicle_age, fitness_upto, pollution_upto, make_model,
                vehicle_class, fuel_type, fuel_norms, ownership, registerd_rto,model_image,owner_name
            FROM vehicle_master
            WHERE registration_no = %s
            """,
            (registration_no,)
        )
        vehicle = cursor.fetchone()
        
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        print(vehicle)

        cursor.execute(
            """
            SELECT *
            FROM vehicles_new
            WHERE registration_no = %s
            """,
            (registration_no,)
        )
        vehicles = cursor.fetchone()
        print(vehicles)

        if not vehicles:
            print("in if")
            cursor.execute(
                """
                INSERT INTO vehicles_new (
                user_id, 
                chassis_no, 
                registration_no, 
                registration_date, 
                engine_no,
                model,
                color
                ,unloaded_weight
                ,rc_status,
                vehicle_age,
                fitness_upto,
                pollution_upto,
                make_model,
                vehicle_class,
                fuel_type,
                fuel_norms,
                ownership,
                registerd_rto,
                model_image,
                owner_name
                )
                VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (user_id,vehicle["chassis_no"],vehicle["registration_no"],vehicle["registration_date"],vehicle["engine_no"],
                vehicle["model"],vehicle["color"],vehicle["unloaded_weight"],vehicle["rc_status"],vehicle["vehicle_age"],
                vehicle["fitness_upto"],vehicle["pollution_upto"],vehicle["make_model"],vehicle["vehicle_class"],vehicle["fuel_type"],
                vehicle["fuel_norms"],vehicle["ownership"],vehicle["registerd_rto"],vehicle["model_image"],vehicle["owner_name"])
            )
            db.commit()
            db.close()

            return vehicle

        else :
            print(user_id)
            print(vehicles['user_id'])
            if(vehicles['user_id'] == user_id):
                data = {
                    "user_id" : None,
                    "owner_name" : vehicles["owner_name"],
                    "model" : vehicles["model"],
                    "registerd_rto" : vehicles["registerd_rto"]
                }
                return data
            else :
                data = {
                    "user_id" : vehicles["user_id"],
                    "owner_name" : vehicles["owner_name"],
                    "model" : vehicles["model"],
                    "registerd_rto" : vehicles["registerd_rto"]
                }
                return data
                

    except Exception as e:
        raise Exception(f"Error in fetch_details_dashboard: {e}")



# This function is used to save the image path, ai, defect, confidence
def insert_vehicle_image(registration_no: str, filename: str, ai_verdict: str, part_name: str, defect: str, confidence: str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        vehicle_id = vehicle['id']

        cursor.execute(
            """
            INSERT INTO vehicle_images(vehicle_id, image_path, part_name, defect, ai_verdict,confidence)
            VALUES (%s, %s, %s, %s, %s,%s)
            """,
            (vehicle_id, filename, part_name, defect, ai_verdict,confidence)
        )

        db.commit()    
        db.close()
    except Exception as e:
        raise Exception(f"Error in insert_vehicle_image: {e}")



# This function is used to update the human response in the 4 table 
def update_human_response(registration_no: str,human_aggregate_verdict:str,part_name:str,status:str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        vehicle_id = vehicle['id']

        cursor.execute(
            """
            UPDATE vehicle_part_verdicts
            SET human_aggregate_verdict = %s,
                human_status = %s
            WHERE vehicle_id = %s AND part_name = %s;
            """,
            (human_aggregate_verdict, status, vehicle_id, part_name)
        )
        db.commit()
        db.close()
    except Exception as e:
        raise Exception(f"Error in update_human_response: {e}")



# This is used to update in 4 table all the final details here
def insert_vehicle_part_verdicts(registration_no: str,part_name:str, ai_aggregate_verdict:str, aggregate_confidence:str,image_count:str,status:str,defect:str,aggregate_confidence_score:str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        vehicle_id = vehicle['id']

        cursor.execute(
            """
            INSERT INTO vehicle_part_verdicts (vehicle_id ,part_name, ai_aggregate_verdict, aggregate_confidence,image_count,status,defect,aggregate_confidence_score)
            VALUES (%s, %s, %s, %s, %s,%s,%s,%s)
            """,
            (vehicle_id ,part_name, ai_aggregate_verdict, aggregate_confidence,image_count,status,defect,aggregate_confidence_score)
        )
        db.commit()
        db.close()
    except Exception as e:
        raise Exception(f"Error in insert_vehicle_part_verdicts: {e}")



def vehicle_mapping(user_id : str, registration_no : str, part_name : str):
    db = None
    cursor = None
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM vehicles_new
            WHERE registration_no = %s
            """,
            (registration_no,)
        )
        vehicle = cursor.fetchone()
        if not vehicle:
            raise Exception("Vehicle not found")

        vehicle_id = vehicle["id"]

        cursor.execute(
            """
            INSERT INTO vehicle_inspection_mapping (vehicle_id, user_id, part_name, status,inspection_timestamp)
            VALUES (%s, %s, %s, 'completd' ,NOW())
            """,
            (vehicle_id, user_id, part_name)
        )
        db.commit()
    except Exception as e:
        raise Exception(f"Error in vehicle_mapping: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()



def view_histroy(registration_no, part_name=None):
    try:
        # Validate inputs
        part_name = part_name[0]
        if part_name is not None and not isinstance(part_name, str):
            raise ValueError("part_name must be a string or None")

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        print("key of registraiton : ", registration_no)

        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                u.username,
                u.first_name,
                u.last_name,
                v.registration_no,
                v.model,
                v.owner_name,
                vpv.part_name,
                GROUP_CONCAT(DISTINCT vi.image_path) AS images,
                vpv.ai_aggregate_verdict AS ai_verdict,
                vpv.human_aggregate_verdict AS human_verdict,
                vpv.status AS status,
                vpv.human_status,
                vpv.defect AS defect,
                vpv.aggregate_confidence AS confidence,
                vpv.aggregate_confidence_score AS confidence_score
            FROM vehicles_new v
            JOIN users u ON v.user_id = u.user_id  
            LEFT JOIN vehicle_part_verdicts vpv ON v.id = vpv.vehicle_id
            LEFT JOIN vehicle_images vi ON v.id = vi.vehicle_id AND vpv.part_name = vi.part_name
            WHERE v.registration_no = %s
        """

        params = [registration_no]

        if part_name:
            query += " AND vpv.part_name = %s"
            params.append(part_name)

        query += """
            GROUP BY 
                vpv.part_name, 
                u.username,
                u.first_name,
                u.last_name, 
                v.registration_no, 
                v.model,
                v.owner_name, 
                vpv.ai_aggregate_verdict, 
                vpv.human_aggregate_verdict, 
                vpv.aggregate_confidence,
                vpv.status,
                vpv.human_status,
                vpv.defect,
                vpv.aggregate_confidence_score
        """

        print("Params for query execution:", params, [type(p) for p in params])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        db.close()

        result = []
        for row in rows:
            images = row["images"].split(",") if row["images"] else []
            images_base64 = [image_path_to_base64(img) for img in images]

            part_json = {
                "username": row["username"],
                "first_name" : row['first_name'],
                "last_name" : row['last_name'],
                "registration_no": row["registration_no"],
                "model": row["model"],
                "owner_name": row["owner_name"],
                "part_name": row["part_name"],
                "ai_verdict": row["ai_verdict"],
                "human_verdict": row["human_verdict"],
                "defect": row["defect"],
                "status": row["status"],
                "human_status" : row["human_status"],
                "confidence": row["confidence"],
                "confidence_score": row["confidence_score"],
                "images": images_base64,

            }
            result.append(part_json)

        return result
    except Exception as e:
        raise Exception(f"Error in histroy: {e}")



def progress_bar_mapping(registration_no: str, user_id : str,completed_status="completd"):
    category_to_parts = {
        "Lighting & Electrical": [
            "Headlamp", "Rear light", "Fog lamp"
        ],
        "Visibility & Driver Aids": [
            "Rear View Mirrors", "Safety Glass (Windscreen)", "Windscreen Wiper"
        ],
        "Dashboard & Monitoring": [
            "Speedometer","Dashboard Equipment"
        ],
        "Structural & Safety": [
            "Suppressor Cap", "Rear Under Run Protection Device (RUPD)", "Spray Suppression Devices"
        ],
        "Markings & Tires": [
            "HSRP", "Tyres", "Retro-reflectors & Reflective Tapes"
        ]
    }

    db = None
    cursor = None
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # here we are bring that vechile from db to tagged user
        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("No vehicle found for this registration number.")

        vehicle_id = vehicle['id']

        # Fetch completed parts for this vehicle
        cursor.execute(
            """
            SELECT DISTINCT part_name
            FROM vehicle_inspection_mapping
            WHERE vehicle_id = %s AND user_id = %s AND status = %s
            """,
            (vehicle_id, user_id, completed_status)
        )
        db_parts = {row['part_name'].strip().lower() for row in cursor.fetchall()}

    except Exception as e:
        if db:
            db.close()
        raise Exception(f"Error fetching progress bar: {e}")

    db.close()

    # Mapping db naming to frontend naming
    db_to_json_part_map = {
        "head lamp": "Headlamp",
        "back light": "Rear light",
        "fog lamp": "Fog lamp",
        "mirror": "Rear View Mirrors",
        "windshield": "Safety Glass (Windscreen)",
        "wiper": "Windscreen Wiper",
        "tyre": "Tyres"
    }

    completed_parts = set()
    for db_part in db_parts:
        json_part = db_to_json_part_map.get(db_part, None)
        if json_part:
            completed_parts.add(json_part)
        else:
            completed_parts.add(db_part.title())

    marked_category_to_parts = {}
    total_parts = 0
    completed_count = 0
    pending_count = 0

    for category, parts in category_to_parts.items():
        new_parts = []
        for part in parts:
            total_parts += 1
            if part in completed_parts:
                new_parts.append({part: "Done"})
                completed_count += 1
            else:
                new_parts.append({part: ""})
                pending_count += 1
        marked_category_to_parts[category] = new_parts

    marked_category_to_parts['total_parts'] = total_parts
    marked_category_to_parts['completed'] = completed_count
    marked_category_to_parts['pending'] = pending_count

    return marked_category_to_parts    



def user_histroy(user_id: str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        key_dict = {}
        count  = 0
        key_count = 0
        # Fetch all vehicles for the user_id
        cursor.execute("SELECT id FROM vehicles_new WHERE user_id = %s", (user_id,))
        vehicles = cursor.fetchall()
        if not vehicles:
            db.close()
            raise ValueError("No vehicles found for this user_id.")

        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                u.username,
                v.registration_no,
                v.model,
                v.owner_name,
                vpv.part_name,
                GROUP_CONCAT(DISTINCT vi.image_path) AS images,
                vpv.ai_aggregate_verdict AS ai_verdict,
                vpv.human_aggregate_verdict AS human_verdict,
                vpv.status AS status,
                vpv.defect AS defect,
                vpv.aggregate_confidence AS confidence,
                vpv.aggregate_confidence_score AS confidence_score
            FROM vehicles_new v
            JOIN users u ON v.user_id = u.user_id
            LEFT JOIN vehicle_part_verdicts vpv ON v.id = vpv.vehicle_id
            LEFT JOIN vehicle_images vi ON v.id = vi.vehicle_id AND vpv.part_name = vi.part_name
            WHERE v.user_id = %s
            GROUP BY 
                v.id,
                vpv.part_name, 
                u.username, 
                v.registration_no, 
                v.model, 
                v.owner_name,
                vpv.ai_aggregate_verdict, 
                vpv.human_aggregate_verdict, 
                vpv.aggregate_confidence,
                vpv.status,
                vpv.defect,
                vpv.aggregate_confidence_score
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        db.close()

        result = {}
        for row in rows:
            reg_no = row["registration_no"]
            if reg_no not in result:
                result[reg_no] = {
                    "username": row["username"],
                    "registration_no": reg_no,
                    "model": row["model"],
                    "owner_name": row["owner_name"],
                    "parts": []
                }
            part_json = {
                "part_name": row["part_name"],
                "images": row["images"].split(",") if row["images"] else [],
                "ai_verdict": row["ai_verdict"],
                "human_verdict": row["human_verdict"],
                "defect": row["defect"],
                "status": row["status"],
                "confidence": row["confidence"],
                "confidence_score": row["confidence_score"]
            }
            result[reg_no]["parts"].append(part_json)

        # Calculate category completion status for each vehicle
        for reg_no, vehicle_info in result.items():
            progress = progress_bar_mapping(reg_no, user_id)
            key_dict = {}  # reset per vehicle to avoid carryover

            # Filter out summary keys
            # category_parts = {k: v for k, v in progress.items() if k not in ['total_parts', 'completed', 'pending']}

            for keys,values in progress.items():
                
                if keys in ['total_parts', 'completed', 'pending']:
                    continue  

                all_done  = True
                count = 0
                key_count  = 1
                for i in values:    
                    # print(i)
                    for k,v in i.items():
                        if (v != "Done"):
                            all_done = False
                            key_count = 0
                            break
                        else :
                            count += 1
                
                print(keys,":",key_count)
                key_dict[keys] = key_count

            vehicle_info['category_completion'] = key_dict

        # Convert the result dict to a list of vehicles
        result_list = [{"vehicle": v} for v in result.values()]

        json_response = json.dumps(result_list, indent=2)
        return result_list

    except Exception as e:
        raise Exception(f"Error in histroy: {e}")


