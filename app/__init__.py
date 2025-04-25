from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import Config

mongo = PyMongo()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)
    
    # Assurez-vous que la clé secrète est bien définie
    if not app.config['SECRET_KEY']:
        raise ValueError("No SECRET_KEY set for Flask application")
    
    mongo.init_app(app)
    login_manager.init_app(app)
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app