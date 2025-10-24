import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_KEY', 'default-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEY = os.getenv('API_KEY')
    ADMIN_USER = os.getenv('ADMIN_USER')
    ADMIN_PASS = os.getenv('ADMIN_PASS')
