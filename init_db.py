import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import requests
from io import BytesIO
from PIL import Image
import base64

# Connexion à MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['location_voitures']

def download_and_resize_image(url, size=(400, 300)):
    """Télécharge et redimensionne une image"""
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.resize(size, Image.LANCZOS)
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def init_collections():
    # Collection users
    users = db['users']
    if users.count_documents({}) == 0:
        admin_user = {
            "username": "admin",
            "email": "admin@location.com",
            "password": generate_password_hash("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        users.insert_one(admin_user)
    
    # Collection voitures avec données plus complètes
    voitures = db['voitures']
    if voitures.count_documents({}) == 0:
        car_images = {
            "toyota": "https://www.toyota.com/imgix/responsive/images/mlp/colorizer/2023/corolla/1.8l/angular-front.png",
            "bmw": "https://www.bmw.fr/content/dam/bmw/marketFR/bmw_fr/all-models/3-series/sedan/2021/overview/bmw-3-series-sedan-sp-desktop.jpg",
            "audi": "https://www.audi.fr/content/dam/nemo/models/a3/a3-sportback/my-2022/1920x1080/1920x1080-a3-sportback-2022-1.jpg",
            "mercedes": "https://www.mercedes-benz.fr/passengercars/mercedes-benz-cars/models/a-class/hatchback-w177/_jcr_content/image.MQ6.12.20211013084329.jpeg"
        }
        
        sample_cars = [
            {
                "marque": "Toyota",
                "modele": "Corolla Hybrid",
                "annee": 2023,
                "prix": 65,
                "disponible": True,
                "image_base64": download_and_resize_image(car_images["toyota"]),
                "description": "Économique et écologique avec une consommation réduite",
                "type": "Hybride",
                "places": 5,
                "transmission": "Automatique",
                "options": ["Climatisation", "GPS", "Caméra de recul", "Régulateur de vitesse"],
                "couleurs": ["Blanc", "Gris", "Noir"],
                "puissance": "140 ch"
            },
            
            {
                "marque": "Audi",
                "modele": "A3 Sportback",
                "annee": 2023,
                "prix": 75,
                "disponible": True,
                "image_base64": download_and_resize_image(car_images["audi"]),
                "description": "Compacte spacieuse avec technologie de pointe",
                "type": "Diesel",
                "places": 5,
                "transmission": "Manuelle",
                "options": ["Apple CarPlay", "Android Auto", "Aide au stationnement"],
                "couleurs": ["Rouge", "Gris", "Blanc"],
                "puissance": "150 ch"
            },
            {
                "marque": "Mercedes",
                "modele": "Classe A",
                "annee": 2023,
                "prix": 85,
                "disponible": False,
                "image_base64": download_and_resize_image(car_images["mercedes"]),
                "description": "Luxe compact avec écrans numériques avancés",
                "type": "Essence",
                "places": 5,
                "transmission": "Automatique",
                "options": ["MBUX", "Sièges massants", "Climatisation 2 zones"],
                "couleurs": ["Noir", "Argent", "Bleu nuit"],
                "puissance": "163 ch"
            }
        ]
        voitures.insert_many(sample_cars)

if __name__ == "__main__":
    init_collections()
    print("Base de données initialisée avec succès avec des données enrichies!")