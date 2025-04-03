import uvicorn
import os
from dotenv import load_dotenv
from app.main import app

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    print("Environment variables loaded:")
    print(f"MONGO_URI: {os.getenv('MONGO_URI')}")
    print(f"MONGO_DB_NAME: {os.getenv('MONGO_DB_NAME')}")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)