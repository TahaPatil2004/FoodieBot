# in backend/config.py
from dotenv import load_dotenv
import os

# This command automatically finds and loads the .env file from the project's root directory
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")