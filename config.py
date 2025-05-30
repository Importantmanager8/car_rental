import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
# Config pour les uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configuration des uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

# Créer le dossier uploads s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# Créez le dossier uploads s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or '035c5c957ce353c1e815b955d832edf85c4e933663e4d22a8224910b321147f4'
    MONGO_URI = os.getenv('MONGO_URI') or 'mongodb://localhost:27017/location_voitures'
    DEBUG = True