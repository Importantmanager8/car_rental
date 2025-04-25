import sys
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId

# Ajoutez le chemin du projet au PATH Python
sys.path.insert(0, '.')

from app import create_app, mongo

def create_admin_account():
    app = create_app()
    
    with app.app_context():
        # Vérifier si l'admin existe déjà
        existing_admin = mongo.db.users.find_one({'email': 'admin@example.com'})
        
        if existing_admin:
            print("Le compte admin existe déjà!")
            return
        
        # Créer le compte admin
        admin_data = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin'
        }
        
        result = mongo.db.users.insert_one(admin_data)
        
        if result.inserted_id:
            print("Compte admin créé avec succès!")
            print(f"ID: {result.inserted_id}")
        else:
            print("Erreur lors de la création du compte admin")

if __name__ == '__main__':
    create_admin_account()