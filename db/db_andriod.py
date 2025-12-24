import base64
import json
import os
from typing import Set
import mysql.connector
from logger import *
import re

# This is the connection function for
# def get_connection():
#     try :
#         return mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="root",
#             database="visual_inspection_solution"
#         )
    
#     except mysql.connector.Error as e:
#         raise Exception(f"Error connecting to database: {e}") 


def get_connection():
    try:
        return mysql.connector.connect(
            # host="172.20.1.216",         # MySQL host
            # user="visual_inspection_user",              # MySQL username
            # password="TbCdgLzp6-91",  # MySQL password
            # database="visual_inspection_solution"   # Your database name
            host="localhost",         # MySQL host
            user="root",              # MySQL username
            password="Root@1234",  # MySQL password
            database="visual_inspection_solution"   # Your database name
    )
    except mysql.connector.Error as e:
        raise Exception(f"Error connecting to database: {e}")


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
def fetch_details_dashboard(registration_no: str, user_id: str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute(
            """
                SELECT 
                    chassis_no,
                    registration_no,
                    registration_date,
                    engine_no,
                    model,
                    color,
                    unloaded_weight,
                    rc_status,
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
                FROM vehicle_master
                WHERE registration_no = %s;


            """,
            (registration_no,)
        )
        vehicle = cursor.fetchone()
        
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        cursor.execute(
            """
            SELECT *
            FROM vehicles_new
            WHERE registration_no = %s
            """,
            (registration_no,)
        )
        vehicles = cursor.fetchone()

        if not vehicles:
            logger.info("Adding new vehicle for inspection")

            cursor.execute(
                """
                INSERT INTO vehicles_new (
                    user_id,
                    chassis_no,
                    registration_no,
                    registration_date,
                    engine_no,
                    model,
                    color,
                    unloaded_weight,
                    rc_status,
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
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );

                """,
                (
                    user_id,
                    vehicle["chassis_no"],
                    vehicle["registration_no"],
                    vehicle["registration_date"],
                    vehicle["engine_no"],
                    vehicle["model"],
                    vehicle["color"],
                    vehicle["unloaded_weight"],
                    vehicle["rc_status"],
                    vehicle["vehicle_age"],
                    vehicle["fitness_upto"],
                    vehicle["pollution_upto"],
                    vehicle["make_model"],
                    vehicle["vehicle_class"],
                    vehicle["fuel_type"],
                    vehicle["fuel_norms"],
                    vehicle["ownership"],
                    vehicle["registerd_rto"],
                    vehicle["model_image"],
                    vehicle["owner_name"]
                )
            )

            db.commit()
            db.close()
            vehicle["vehicle_isnpected"] = False
            return vehicle

        else:

            vehicle_inpected = progress_bar_mapping(registration_no,user_id)
            completed_parts = vehicle_inpected["completed"]
            pending = vehicle_inpected["pending"]
            
            vehicle_id = vehicles["id"]
            print(vehicle_id)
            cursor.execute(
                """
                SELECT COUNT(image_path)
                FROM vehicle_images
                WHERE vehicle_id = %s
                """,
                (vehicle_id,)
            )
            vehicles_count = cursor.fetchone()
            # print(vehicles_count["COUNT(image_path)"])

            if vehicles['user_id'] == user_id:
                return {
                    "user_id": "same_user",
                    "owner_name": vehicles["owner_name"],
                    "model": vehicles["model"],
                    "registerd_rto": vehicles["registerd_rto"],
                    "vehicle_isnpected" : True,
                    "completed_parts" : completed_parts,
                    "pending" : pending,
                    "images_count" : vehicles_count["COUNT(image_path)"]

                }
            else:
                return {
                    "user_id": vehicles["user_id"],
                    "owner_name": vehicles["owner_name"],
                    "model": vehicles["model"],
                    "registerd_rto": vehicles["registerd_rto"],
                    "vehicle_isnpected" : True,
                    "completed_parts" : completed_parts,
                    "pending" : pending,
                    "images_count" : vehicles_count
                }

    except Exception as e:
        raise Exception(f"Error in fetch_details_dashboard: {e}")



def insert_vehicle_image(registration_no: str, user_id: int, filename: str, part_name: str, status: bool):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        inspection_id = None
        # Get vehicle_id from registration_no
        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        vehicle_id = vehicle['id']

        cursor.execute("""
            INSERT INTO vehicle_images(vehicle_id, part_name, image_path, status)
            VALUES (%s, %s, %s, %s)
        """, (vehicle_id, part_name,filename,status))

        logger.info(f"Inserted image '{filename}' for vehicle '{registration_no}', part '{part_name}', status={status}")

        db.commit()
        db.close()
    except Exception as e:
        raise Exception(f"Error in insert_vehicle_image: {e}")





# This function is used to update the human response in the 4 table 
def update_human_response(registration_no: str,part_name:str,status:str,human_aggregate_verdict=None):
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
            UPDATE vehicle_images
            SET human_verdict = %s,
                human_desicion = %s
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



def view_history_db(registration_no, part_name=None):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        print(registration_no)
        # Find vehicle ID from registration_no
        cursor.execute("SELECT id, user_id, model, owner_name FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        print(vehicle)
        if not vehicle:
            db.close()
            raise ValueError("Vehicle not found for registration number")

        vehicle_id = vehicle["id"]
        user_id = vehicle["user_id"]

        # Base query selects from inspection mapping joined with images and users
        query = """
            SELECT 
                u.username,
                u.first_name,
                u.last_name,
                v.registration_no,
                v.model,
                v.owner_name,
                vim.part_name,
                vim.status,
                vim.category_name,
                vim.inspection_timestamp,
                vi.image_path,
                vi.defect,
                vi.ai_verdict,
                vi.human_verdict,
                vi.human_desicion,
                vi.confidence,
                vi.uploaded_at
            FROM vehicle_inspection_mapping vim
            LEFT JOIN vehicle_images vi ON vim.vehicle_id = vi.vehicle_id AND vim.part_name = vi.part_name
            JOIN vehicles_new v ON vim.vehicle_id = v.id
            JOIN users u ON vim.user_id = u.user_id
            WHERE vim.vehicle_id = %s
        """

        params = [vehicle_id]

        # Filter by part_name if provided
        if part_name:
            query += " AND vim.part_name = %s"
            params.append(part_name)

        # Order by inspection timestamp desc, part name etc.
        query += " ORDER BY vim.inspection_timestamp DESC, vim.part_name ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        db.close()

        # Process rows grouping only by part_name
        results = []
        part_map = {}

        for row in rows:
            part_key = row["part_name"]
            if part_key not in part_map:
                part_map[part_key] = {
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "registration_no": row["registration_no"],
                    "model": row["model"],
                    "owner_name": row["owner_name"],
                    "part_name": row["part_name"],
                    "status": row["status"],
                    "category_name": row["category_name"],
                    "inspection_timestamps": [],
                    "images": [],
                    "human_desicion" : row["human_desicion"],
                    "defects": set(),
                    "ai_verdict": None,
                    "human_verdict": row["human_verdict"],
                    "confidence": None,
                }
            # Append the current inspection timestamp if it exists and is new
            if row["inspection_timestamp"] and row["inspection_timestamp"] not in part_map[part_key]["inspection_timestamps"]:
                part_map[part_key]["inspection_timestamps"].append(row["inspection_timestamp"].isoformat())
            # Append images
            if row["image_path"]:
                part_map[part_key]["images"].append(row["image_path"])
            # Collect defects
            if row["defect"]:
                part_map[part_key]["defects"].add(row["defect"])
            # Aggregate or update verdicts
            if not part_map[part_key]["ai_verdict"]:
                part_map[part_key]["ai_verdict"] = row["ai_verdict"]
            if not part_map[part_key]["human_verdict"]:
                part_map[part_key]["human_verdict"] = row["human_verdict"]
            if not part_map[part_key]["confidence"]:
                part_map[part_key]["confidence"] = row["confidence"]

        # Convert defects to lists for JSON serializability and convert images to base64
        for part in part_map.values():
            part["defects"] = list(part["defects"])
            # CONVERT IMAGE PATHS TO BASE64 HERE:
            part["images"] = [image_path_to_base64(img) for img in part["images"]]
            results.append(part)

        return results

    except Exception as e:
        raise Exception(f"Error in history: {e}")




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
        "front_headlamp": "Headlamp",
        "car_backlight": "Rear light",
        "fog_lamp": "Fog lamp",
        "mirror": "Rear View Mirrors",
        "windshield": "Safety Glass (Windscreen)",
        "wiper": "Windscreen Wiper",
        "tyre": "Tyres",
        "reflector" : "Retro-reflectors & Reflective Tapes",
        "hsrp" : "HSRP",
        "speedometer" : "Speedometer",
        "dashboard" : "Dashboard Equipment",
        "rupd" : "Rear Under Run Protection Device (RUPD)",
        "suppressor_cap" : "Suppressor Cap",
        "suppressor_devices" : "Spray Suppression Devices",
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



def user_history(user_id: str):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch all vehicles for the user_id
        cursor.execute("SELECT id, registration_no FROM vehicles_new WHERE user_id = %s", (user_id,))
        vehicles = cursor.fetchall()
        if not vehicles:
            db.close()
            # raise ValueError("No vehicles found for this user_id.")
            return None

        # Query from vehicle_inspection_mapping and vehicle_images
        query = """
            SELECT 
                u.username,
                v.registration_no,
                v.model,
                v.owner_name,
                vim.part_name,
                GROUP_CONCAT(DISTINCT vi.image_path) AS images,
                vim.status,
                vim.category_name,
                vim.inspection_timestamp,
                vim.user_id,
                vim.vehicle_id,
                vi.defect,
                vi.ai_verdict,
                vi.human_verdict,
                vi.confidence
            FROM vehicles_new v
            JOIN users u ON v.user_id = u.user_id
            LEFT JOIN vehicle_inspection_mapping vim ON v.id = vim.vehicle_id
            LEFT JOIN vehicle_images vi ON vim.vehicle_id = vi.vehicle_id AND vim.part_name = vi.part_name
            WHERE v.user_id = %s
            GROUP BY 
                v.id,
                vim.part_name, 
                u.username, 
                v.registration_no, 
                v.model, 
                v.owner_name,
                vim.status,
                vim.category_name,
                vim.inspection_timestamp,
                vim.user_id,
                vim.vehicle_id,
                vi.defect,
                vi.ai_verdict,
                vi.human_verdict,
                vi.confidence
            ORDER BY vim.inspection_timestamp DESC, vim.part_name ASC
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
                "ai_verdict": row.get("ai_verdict"),
                "human_verdict": row.get("human_verdict"),
                "defect": row.get("defect"),
                "status": row.get("status"),
                "confidence": row.get("confidence")
            }
            result[reg_no]["parts"].append(part_json)

        # Add image count for each vehicle
        for reg_no in result:
            vehicle_id = [v["id"] for v in vehicles if v["registration_no"] == reg_no][0]
            print(f"Debug: Fetching image count for vehicle_id: {vehicle_id}, registration_no: {reg_no}")
            db = get_connection()
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT COUNT(image_path)
                FROM vehicle_images
                WHERE vehicle_id = %s
                """,
                (vehicle_id,)
            )
            vehicles_count = cursor.fetchone()
            image_count = vehicles_count[0] if vehicles_count else 0
            result[reg_no]["image_count"] = image_count
            print(f"Debug: Image count for {reg_no}: {image_count}")
            db.close()

        # You can keep or modify progress_bar_mapping logic if relevant to new table data
        for reg_no, vehicle_info in result.items():
            progress = progress_bar_mapping(reg_no, user_id)
            key_dict = {}  # reset per vehicle to avoid carryover
            for keys, values in progress.items():
                if keys in ['total_parts', 'completed', 'pending']:
                    continue
                all_done = True
                key_count = 1
                for i in values:    
                    for k,v in i.items():
                        if v != "Done":
                            all_done = False
                            key_count = 0
                            break
                    if not all_done:
                        break
                key_dict[keys] = key_count
            vehicle_info['category_completion'] = key_dict

        # Convert the result dict to a list of vehicles
        result_list = [{"vehicle": v} for v in result.values()]

        if not result_list:
            print("In result lsit")
            return None
        
        return result_list

    except Exception as e:
        print(f"Error in history: {e}")
        raise Exception(f"Error in history: {str(e)}")



def human_status_updater(registration_no: str, user_id: int,part_name: str, human_status: str,status="Completed"):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        inspection_id = None
        # Get vehicle_id from registration_no
        cursor.execute("SELECT id FROM vehicles_new WHERE registration_no = %s", (registration_no,))
        vehicle = cursor.fetchone()
        if not vehicle:
            db.close()
            raise ValueError("Vehicle with registration_no not found")

        vehicle_id = vehicle['id']

        # Get part_id from part_name
        cursor.execute("SELECT part_id FROM parts_master WHERE part_name = %s", (part_name,))
        part = cursor.fetchone()
        if not part:
            db.close()
            raise ValueError("Part with given part_name not found")

        part_id = part['part_id']

        # Find active inspection for vehicle and user
        cursor.execute("""
            SELECT inspection_id FROM inspections 
            WHERE vehicle_id = %s AND user_id = %s AND status = 'Active' LIMIT 1
        """, (vehicle_id, user_id))
        inspection = cursor.fetchone()

        # Create new inspection if none active
        if inspection:
            inspection_id = inspection['inspection_id']

        cursor.execute("""
            INSERT INTO vehicle_part_verdicts (vehicle_id,inspection_id, part_id, human_status,status)
            VALUES (%s, %s, %s, %s,%s)
        """, (vehicle_id,inspection_id, part_id, human_status,status    ))

        logger.info(f"Inserted verdict for vehicle '{registration_no}', part '{part_name}', human_status={human_status}")

        db.commit()
        db.close()
    except Exception as e:
        raise Exception(f"Error in human_status api : {e}")
    

def get_part_images(user_id: int, vehicle_id: int):

    try :
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # Verify vehicle ownership
        cursor.execute(
            "SELECT id FROM vehicles_new WHERE id = %s AND user_id = %s",
            (vehicle_id, user_id)
        )
        vehicle = cursor.fetchone()
        if not vehicle:
            cursor.close()
            db.close()
            raise Exception(status_code=404, detail=f"Vehicle ID {vehicle_id} not found for User ID {user_id}")

        # Get images for vehicle
        cursor.execute(
            """
            SELECT image_path, part_name, status, uploaded_at,human_desicion,human_verdict
            FROM vehicle_images
            WHERE vehicle_id = %s
            """,
            (vehicle_id,)
        )
        records = cursor.fetchall()

        cursor.close()
        db.close()

        return records
    
    except Exception as eobj:
        raise Exception(f"Error occured in the Get Images Services fuction")



def dashboard_car_detials(registration_no: str, user_id: str):
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

        # If NOT inspected earlier → fetch from vehicle_master
        if not vehicles:
            cursor.execute(
                """
                SELECT 
                    chassis_no,
                    registration_no,
                    registration_date,
                    engine_no,
                    model,
                    color,
                    unloaded_weight,
                    rc_status,
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
                FROM vehicle_master
                WHERE registration_no = %s
                """,
                (registration_no,)
            )
            vehicle = cursor.fetchone()

            print("In db (master)", vehicle)

            if not vehicle:
                db.close()
                raise ValueError("Vehicle with registration_no not found")

            vehicle["inspected"] = False
            return vehicle
        
        # If inspected earlier → vehicles_new
        else:
            vehicles["inspected"] = True
            print("In db (vehicles_new)", vehicles)
            return vehicles

    except Exception as e:
        raise Exception(f"Error in fetch_details_dashboard: {e}")


def part_image(vehicle_id: int,part_name: str):
    try :
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # Verify vehicle ownership
        cursor.execute(
            "SELECT id FROM vehicles_new WHERE id = %s",
            (vehicle_id,)
        )
        vehicle = cursor.fetchone()
        print(vehicle["id"])
        if not vehicle:
            cursor.close()
            db.close()
            raise Exception(status_code=404, detail=f"Vehicle ID {vehicle_id}")

        # Get images for vehicle
        cursor.execute(
            """
            SELECT image_path, part_name, status, uploaded_at,human_desicion,human_verdict
            FROM vehicle_images
            WHERE vehicle_id = %s AND part_name = %s
            """,
            (vehicle_id,part_name)
        )
        record = cursor.fetchone()
        
        if not record:
            logger.error("No Image found for that part name.")
            return None

        cursor.close()
        db.close()

        logger.info(f"Image returned from the DB to API for partname : {part_name} and vehicle id : {vehicle_id}")
        return record
    
    except Exception as eobj:
        raise Exception(f"Error occured in the part image fucntion")
    
    

def check_imageupload(registration_no:str,part_name:str):
    try :
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # Verify vehicle ownership
        cursor.execute(
            "SELECT id FROM vehicles_new WHERE registration_no = %s",
            (registration_no,)
        )
        vehicle = cursor.fetchone()
        vehicle_id = vehicle["id"]
        print(vehicle["id"])
        
        if not vehicle:
            cursor.close()
            db.close()
            raise Exception(status_code=404, detail=f"Vehicle registration_no {registration_no}")

        # Get images for vehicle
        cursor.execute(
            """
            SELECT uploaded
            FROM vehicle_images
            WHERE vehicle_id = %s AND part_name = %s
            """,
            (vehicle_id,part_name)
        )
        record = cursor.fetchone()
        print(record)
        if not record:
            logger.error("No Image found for that part name.")
            return None

        cursor.close()
        db.close()
        
        return record
    
    except Exception as eobj:
        raise Exception(f"Error occured in the part image fucntion")
    