from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from web API
from app.web_api.dashboard import router as dashboard_router_web
from app.web_api.human_response import router as human_response_router_web
from app.web_api.imageupload import router as upload_image_router_web
from app.web_api.progress_bar import router as progress_bar_router_web
from app.web_api.user_history import router as user_history_router_web
from app.web_api.user import router as user_router_web
from app.web_api.view_part_history import router as history_router_web

# Import routers from android API
from app.android_api.dashboard import router as dashboard_router
from app.android_api.imageupload_1 import router as upload_image_router
from app.android_api.progress_bar import router as progress_bar_router
from app.android_api.user_history import router as user_history_router
from app.android_api.user import router as user_router
from app.android_api.view_part_history import router as history_router
from app.android_api.human_status import router as human_status_router
from app.android_api.get_images import router as get_images_router
from app.android_api.dashboard_first import router as dashboard_car_getdetials
from app.android_api.get_one_image import router as getpart_image

app = FastAPI()

#android API routers
app.include_router(dashboard_router)
app.include_router(upload_image_router)
app.include_router(progress_bar_router)
app.include_router(user_history_router)
app.include_router(user_router)
app.include_router(history_router)
app.include_router(human_status_router)
app.include_router(get_images_router)
app.include_router(dashboard_car_getdetials)
app.include_router(getpart_image)
#web API routers
app.include_router(dashboard_router_web)
app.include_router(human_response_router_web)
app.include_router(upload_image_router_web)
app.include_router(progress_bar_router_web)
app.include_router(user_history_router_web)
app.include_router(user_router_web)
app.include_router(history_router_web)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://172.20.1.45:8001",
    "http://172.20.1.228:8013",
    "http://172.20.1.30:8081",  # Replace 3000 with your frontend port if different

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
