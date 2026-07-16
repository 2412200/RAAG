import os
from dotenv import load_dotenv
import razorpay
# Load environment variables
load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret_key_please_change")
    ALGORITHM: str = "HS256"
    
    # Postgres
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "")
    
    # MongoDB
    MONGO_USERNAME: str = os.getenv("MONGO_USERNAME", "")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
    MONGO_CLUSTER: str = os.getenv("MONGO_CLUSTER", "")
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    # Twilio
    ACCOUNT_SID: str = os.getenv("ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("Twilio_auth_token", "")  # matches Twilio_auth_token in .env
    TWILIO_VERIFY_SERVICE_SID: str = os.getenv("TWILIO_VERIFY_SERVICE_SID", "VA8615c88e13880d52c82e08acb4f51171")
    
    # Razorpay Credentials
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    
    #Razorpay
    razorpay_client = razorpay.Client(
        auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
    )
    
    # CORS (can add specific domains in production, e.g. ["https://myfrontend.com"])
    ALLOWED_ORIGINS: list[str] = ["*"]

SETTINGS = Settings()
