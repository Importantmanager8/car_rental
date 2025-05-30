from datetime import datetime
from bson import ObjectId

voiture_schema = {
    'type': 'object',
    'required': ['marque', 'modele', 'annee', 'prix'],
    'properties': {
        'marque': {'type': 'string', 'minLength': 2},
        'modele': {'type': 'string', 'minLength': 1},
        'annee': {'type': 'integer', 'minimum': 1900, 'maximum': datetime.now().year + 1},
        'prix': {'type': 'number', 'minimum': 0},
        'options': {
            'type': 'array',
            'items': {'type': 'string', 'enum': [
                'climatisation',
                'gps',
                'sieges_chauffants',
                'toit_ouvrant',
                'camera_recul'
            ]}
        },
        'disponible': {'type': 'boolean'},
        'image_url': {'type': 'string'}
    }
}