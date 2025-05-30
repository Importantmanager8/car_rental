from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import mongo
from bson import ObjectId
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password']
        self.role = user_data['role']
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    @staticmethod
    def get_by_id(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None
class Voiture:
    def __init__(self, data):
        self._id = data.get('_id')
        self.marque = data.get('marque')
        self.modele = data.get('modele')
        self.annee = data.get('annee')
        self.prix = data.get('prix')
        self.description = data.get('description', '')
        self.options = data.get('options', [])
        self.disponible = data.get('disponible', True)
        self.images = data.get('images', [])  # Liste des URLs des images
        self.image_principale = data.get('image_principale')  # Image principale

    @staticmethod
    def create(marque, modele, annee, prix, options=None, disponible=True, image_url=None, description=''):
        voiture_data = {
            'marque': marque,
            'modele': modele,
            'annee': annee,
            'prix': prix,
            'options': options or [],
            'disponible': disponible,
            'description': description,
            'images': [image_url] if image_url else [],
            'image_principale': image_url if image_url else None,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.voitures.insert_one(voiture_data)
        return result.inserted_id

    @staticmethod
    def add_image(voiture_id, image_url, is_principal=False):
        update = {
            '$addToSet': {'images': image_url}
        }
        if is_principal:
            update['$set'] = {'image_principale': image_url}
        
        return mongo.db.voitures.update_one(
            {'_id': ObjectId(voiture_id)},
            update
        )

    @staticmethod
    def remove_image(voiture_id, image_url):
        update = {
            '$pull': {'images': image_url}
        }
        
        # Si l'image principale est supprimée, la remplacer par la première image restante
        voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
        if voiture and voiture.get('image_principale') == image_url:
            remaining_images = [img for img in voiture.get('images', []) if img != image_url]
            update['$set'] = {'image_principale': remaining_images[0] if remaining_images else None}
        
        return mongo.db.voitures.update_one(
            {'_id': ObjectId(voiture_id)},
            update
        )

    @staticmethod
    def get_by_id(voiture_id):
        voiture_data = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
        return Voiture(voiture_data) if voiture_data else None

    def add_option(self, option_name):
        mongo.db.voitures.update_one(
            {'_id': ObjectId(self._id)},
            {'$addToSet': {'options': option_name}}
        )

    def remove_option(self, option_name):
        mongo.db.voitures.update_one(
            {'_id': ObjectId(self._id)},
            {'$pull': {'options': option_name}}
        )
class Reservation:
    @staticmethod
    def get_user_reservations(user_id):
        return list(mongo.db.reservations.find({
            '$or': [
                {'user_id': user_id},
                {'client_id': user_id}
            ]
        }).sort('date_debut', -1))

    @staticmethod
    def get_all_with_details():
        return list(mongo.db.reservations.aggregate([
            {
                '$lookup': {
                    'from': 'voitures',
                    'localField': 'voiture_id',
                    'foreignField': '_id',
                    'as': 'voiture'
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {
                '$unwind': {
                    'path': '$voiture',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$unwind': {
                    'path': '$user',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$sort': {'date_debut': -1}
            }
        ]))