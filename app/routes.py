from datetime import datetime
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, send_file, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app import mongo, login_manager
from app.forms import LoginForm, RegistrationForm, VoitureForm, ReservationForm,ManagerForm
from app.models import User
from datetime import datetime
from bson.objectid import ObjectId
from datetime import datetime  # Ajoutez cet import en haut du fichier
from werkzeug.utils import secure_filename  # For secure filename handling
import os  # For path operations
from .models import Voiture
from .forms import VoitureForm
# Création du Blueprint
main_bp = Blueprint('main', __name__)

# Configuration du user_loader
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user_data:
        return None
    return User(user_data)


@main_bp.route('/')
@login_required  # Bloque l'accès aux non-connectés
def index():
    # Rediriger en fonction du rôle
    if current_user.role == 'admin':
        managers = list(mongo.db.users.find({'role': 'manager'}))
        return render_template('index.html', managers=managers)
    elif current_user.role == 'manager':
        voitures = list(mongo.db.voitures.find({'disponible': True}))
        return render_template('index.html', voitures=voitures)
    else:
        # Cas par défaut (si d'autres rôles existent)
        flash("Vous n'avez pas les permissions nécessaires", 'danger')
        return redirect(url_for('main.logout'))  # Déconnecte les utilisateurs non autorisés

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_data = mongo.db.users.find_one({'email': form.email.data})
        if user_data and check_password_hash(user_data['password'], form.password.data):
            user = User(user_data)
            login_user(user)
            next_page = request.args.get('next')
            
            # Redirection en fonction du rôle
            if not next_page:
                if user.role == 'admin':
                    next_page = url_for('main.gestion_managers')
                elif user.role == 'manager':
                    next_page = url_for('main.gestion_reservations')
                else:
                    next_page = url_for('main.index')
            
            return redirect(next_page)
        flash('Email ou mot de passe incorrect', 'danger')
    return render_template('login.html', form=form)
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_data = mongo.db.users.find_one({'email': form.email.data})
        if user_data and check_password_hash(user_data['password'], form.password.data):
            user = User(user_data)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        flash('Email ou mot de passe incorrect', 'danger')
    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur"""
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    print("Inscription d'un nouvel utilisateur")
    """Inscription de nouveaux utilisateurs"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    print(form)
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password,
            'role': 'client'
        }
        mongo.db.users.insert_one(user_data)
        flash('Votre compte a été créé avec succès!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main_bp.route('/voiture')
def voitures():
    """Liste des voitures disponibles"""
    voitures = list(mongo.db.voitures.find())
    
    # Récupérer les valeurs uniques pour les filtres
    marques_uniques = sorted(list(set(v['marque'] for v in voitures)))
    types_uniques = sorted(list(set(v.get('type', '') for v in voitures if v.get('type'))))
    prix_max = max(v['prix'] for v in voitures) if voitures else 0
    
    return render_template('voiture/voitures.html', 
                         voitures=voitures,
                         marques_uniques=marques_uniques,
                         types_uniques=types_uniques,
                         prix_max=prix_max)

# Supprimez les doublons de la route /reserver
@main_bp.route('/reserver/<voiture_id>', methods=['GET', 'POST'])
@login_required
def reserver(voiture_id):
    # Vérifier que la voiture existe et est disponible
    voiture = mongo.db.voitures.find_one({
        '_id': ObjectId(voiture_id),
        'disponible': True
    })
    
    if not voiture:
        flash('Voiture non trouvée ou non disponible', 'danger')
        return redirect(url_for('main.voitures'))

    form = ReservationForm()
    form.voiture_id.choices = [(str(voiture['_id']), f"{voiture['marque']} {voiture['modele']}")]

    if form.validate_on_submit():
        try:
            # Validation et conversion des dates
            date_debut = datetime.combine(form.date_debut.data, datetime.min.time())
            date_fin = datetime.combine(form.date_fin.data, datetime.min.time())
            
            # Vérification que la date de début est future
            if date_debut < datetime.now():
                flash('La date de début doit être future', 'danger')
                return redirect(url_for('main.reserver', voiture_id=voiture_id))
            
            # Vérification que la date de fin est après la date de début
            if date_fin <= date_debut:
                flash('La date de fin doit être après la date de début', 'danger')
                return redirect(url_for('main.reserver', voiture_id=voiture_id))

            # Calcul de la durée et du prix
            delta = date_fin - date_debut
            jours = delta.days
            if jours < 1:
                flash('La durée doit être d\'au moins 1 jour', 'danger')
                return redirect(url_for('main.reserver', voiture_id=voiture_id))
            
            total = jours * voiture['prix']
            
            # Vérifier une dernière fois que la voiture est toujours disponible
            voiture_dispo = mongo.db.voitures.find_one({
                '_id': ObjectId(voiture_id),
                'disponible': True
            })
            
            if not voiture_dispo:
                flash('Désolé, cette voiture vient d\'être réservée', 'warning')
                return redirect(url_for('main.voitures'))
            
            # Création réservation
            reservation_data = {
                'client_nom': form.client_nom.data,
                'voiture_id': ObjectId(voiture_id),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'prix_total': total,
                'status': 'en_attente',
                'created_at': datetime.utcnow()
            }
            
            # Insérer la réservation
            result = mongo.db.reservations.insert_one(reservation_data)
            
            if result.inserted_id:
                # Mise à jour disponibilité voiture
                update_result = mongo.db.voitures.update_one(
                    {'_id': ObjectId(voiture_id)},
                    {'$set': {'disponible': False}}
                )
                
                if update_result.modified_count > 0:
                    flash('Réservation effectuée avec succès!', 'success')
                else:
                    # Si la mise à jour de la voiture échoue, supprimer la réservation
                    mongo.db.reservations.delete_one({'_id': result.inserted_id})
                    flash('Erreur lors de la réservation, veuillez réessayer', 'danger')
                    return redirect(url_for('main.voitures'))
            else:
                flash('Erreur lors de la création de la réservation', 'danger')
                return redirect(url_for('main.voitures'))
            
            return redirect(url_for('main.gestion_reservations'))
            
        except Exception as e:
            flash(f"Erreur lors de la réservation: {str(e)}", 'danger')
            return redirect(url_for('main.voitures'))

    # Pré-remplir le nom si utilisateur connecté
    if current_user.is_authenticated:
        form.client_nom.data = current_user.username
    
    return render_template('reservation/gestion_reservations.html', form=form, voiture=voiture)



@main_bp.route('/voiture/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_voiture():
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = VoitureForm()
    if form.validate_on_submit():
        try:
            # Traitement des images
            image_urls = []
            image_principale = None
            
            if form.images.data:
                for image in form.images.data:
                    if image:
                        # Sécuriser le nom du fichier
                        filename = secure_filename(image.filename)
                        # Ajouter un timestamp pour éviter les doublons
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        filename = f"{timestamp}_{filename}"
                        
                        # Sauvegarder l'image
                        image_path = os.path.join('app', 'static', 'images', filename)
                        image.save(image_path)
                        
                        # Ajouter l'URL à la liste
                        image_url = f'images/{filename}'
                        image_urls.append(image_url)
                        
                        # Si c'est la première image, la définir comme principale
                        if not image_principale:
                            image_principale = image_url

            # Traitement des options
            options = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()] if form.options.data else []

            # Création de la voiture avec conversion du prix en float
            voiture_id = Voiture.create(
                marque=form.marque.data,
                modele=form.modele.data,
                annee=form.annee.data,
                prix=float(form.prix.data),  # Conversion de Decimal en float
                description=form.description.data,
                options=options,
                disponible=form.disponible.data,
                image_url=image_principale
            )

            # Ajouter les images supplémentaires
            for image_url in image_urls[1:]:  # Skip the first one as it's already set as principal
                Voiture.add_image(voiture_id, image_url)

            flash('Voiture ajoutée avec succès!', 'success')
            return redirect(url_for('main.gestion_voitures'))

        except Exception as e:
            flash(f'Erreur lors de l\'ajout de la voiture: {str(e)}', 'danger')

    return render_template('voiture/ajouter_voiture.html', form=form)


@main_bp.route('/image/<path:filename>')
def image_from_path(filename):
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(full_path):
        return abort(404)
    return send_file(full_path)

@main_bp.route('/voiture/modifier_voiture/<voiture_id>', methods=['GET', 'POST'])
@login_required
def modifier_voiture(voiture_id):
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
    if not voiture:
        flash('Voiture non trouvée', 'danger')
        return redirect(url_for('main.gestion_voitures'))

    form = VoitureForm()
    
    # Pour le sélecteur d'image principale
    if request.method == 'GET':
        form.image_principale.choices = [(img, f"Image {i+1}") for i, img in enumerate(voiture.get('images', []))]

    if form.validate_on_submit():
        try:
            # Traitement des nouvelles images
            if form.images.data:
                for image in form.images.data:
                    if image:
                        filename = secure_filename(image.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        filename = f"{timestamp}_{filename}"
                        
                        image_path = os.path.join('app', 'static', 'images', filename)
                        image.save(image_path)
                        
                        image_url = f'images/{filename}'
                        Voiture.add_image(voiture_id, image_url)

            # Mise à jour de l'image principale si sélectionnée
            if form.image_principale.data:
                mongo.db.voitures.update_one(
                    {'_id': ObjectId(voiture_id)},
                    {'$set': {'image_principale': form.image_principale.data}}
                )

            # Traitement des options
            options = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()] if form.options.data else []

            # Mise à jour des autres champs
            update_data = {
                'marque': form.marque.data,
                'modele': form.modele.data,
                'annee': form.annee.data,
                'prix': float(form.prix.data),  # Conversion de Decimal en float
                'description': form.description.data,
                'options': options,
                'disponible': form.disponible.data,
                'updated_at': datetime.utcnow()
            }

            mongo.db.voitures.update_one(
                {'_id': ObjectId(voiture_id)},
                {'$set': update_data}
            )

            flash('Voiture mise à jour avec succès!', 'success')
            return redirect(url_for('main.gestion_voitures'))

        except Exception as e:
            flash(f'Erreur lors de la modification: {str(e)}', 'danger')

    elif request.method == 'GET':
        # Pré-remplir le formulaire
        form.marque.data = voiture.get('marque')
        form.modele.data = voiture.get('modele')
        form.annee.data = voiture.get('annee')
        form.prix.data = voiture.get('prix')
        form.description.data = voiture.get('description')
        form.disponible.data = voiture.get('disponible', True)
        form.options.data = '\n'.join(voiture.get('options', []))

    return render_template('voiture/modifier_voiture.html', form=form, voiture=voiture)

@main_bp.route('/voiture/supprimer_image/<voiture_id>/<path:image_url>')
@login_required
def supprimer_image(voiture_id, image_url):
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    try:
        # Supprimer le fichier physique
        image_path = os.path.join('app', 'static', image_url)
        if os.path.exists(image_path):
            os.remove(image_path)

        # Supprimer la référence dans la base de données
        Voiture.remove_image(voiture_id, image_url)
        
        flash('Image supprimée avec succès', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression de l\'image: {str(e)}', 'danger')

    return redirect(url_for('main.modifier_voiture', voiture_id=voiture_id))

@main_bp.route('/supprimer_voiture/<voiture_id>')
@login_required
def supprimer_voiture(voiture_id):
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    mongo.db.voitures.delete_one({'_id': ObjectId(voiture_id)})
    flash('Voiture supprimée avec succès', 'success')
    return redirect(url_for('main.gestion_voitures'))

# Section Manager
@main_bp.route('/gestion/voitures', methods=['GET', 'POST'])
@login_required
def gestion_voitures():
    """Gestion des voitures (accès réservé aux managers)"""
    if current_user.role != 'manager':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    voitures = list(mongo.db.voitures.find())
    return render_template('voiture/gestion_voitures.html', voitures=voitures)

@main_bp.route('/gestion/reservations', methods=['GET', 'POST'])
@login_required
def gestion_reservations():
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    # Gestion du formulaire
    form = ReservationForm()
    voitures = list(mongo.db.voitures.find({'disponible': True}))
    form.voiture_id.choices = [(str(v['_id']), f"{v['marque']} {v['modele']} - {v['prix']}€/jour") for v in voitures]

    if form.validate_on_submit():
        try:
            # Validation des dates
            date_debut = datetime.combine(form.date_debut.data, datetime.min.time())
            date_fin = datetime.combine(form.date_fin.data, datetime.min.time())
            
            # Vérification que la date de début est future
            if date_debut < datetime.now():
                flash('La date de début doit être future', 'danger')
                return redirect(url_for('main.gestion_reservations'))
            
            # Vérification que la date de fin est après la date de début
            if date_fin <= date_debut:
                flash('La date de fin doit être après la date de début', 'danger')
                return redirect(url_for('main.gestion_reservations'))

            # Calcul du prix total
            delta = date_fin - date_debut
            jours = delta.days
            if jours < 1:
                flash('La durée de réservation doit être d\'au moins 1 jour', 'danger')
                return redirect(url_for('main.gestion_reservations'))

            # Vérifier que la voiture existe et est toujours disponible
            voiture = mongo.db.voitures.find_one({
                '_id': ObjectId(form.voiture_id.data),
                'disponible': True
            })
            
            if not voiture:
                flash('Cette voiture n\'est plus disponible', 'danger')
                return redirect(url_for('main.gestion_reservations'))

            total = jours * voiture['prix']
            
            # Créer la réservation
            reservation_data = {
                'client_nom': form.client_nom.data,
                'voiture_id': ObjectId(form.voiture_id.data),
                'date_debut': date_debut,  # Now using datetime object instead of date
                'date_fin': date_fin,      # Now using datetime object instead of date
                'prix_total': total,
                'status': 'en_attente',
                'created_at': datetime.utcnow()
            }
            
            # Insérer la réservation
            result = mongo.db.reservations.insert_one(reservation_data)
            
            if result.inserted_id:
                # Mettre à jour la disponibilité de la voiture
                mongo.db.voitures.update_one(
                    {'_id': ObjectId(form.voiture_id.data)},
                    {'$set': {'disponible': False}}
                )
                flash('Réservation créée avec succès!', 'success')
            else:
                flash('Erreur lors de la création de la réservation', 'danger')
            
            return redirect(url_for('main.gestion_reservations'))
            
        except Exception as e:
            flash(f"Erreur lors de la création: {str(e)}", 'danger')

    # Récupération des réservations avec jointures
    reservations = list(mongo.db.reservations.aggregate([
        {
            '$lookup': {
                'from': 'voitures',
                'localField': 'voiture_id',
                'foreignField': '_id',
                'as': 'voiture'
            }
        },
        {'$unwind': '$voiture'},
        {'$sort': {'date_debut': -1}}
    ]))

    return render_template('reservation/gestion_reservations.html',
                         form=form,
                         reservations=reservations,
                         voitures=voitures)

@main_bp.route('/gestion/reservation/<reservation_id>/<status>')
@login_required
def changer_statut_reservation(reservation_id, status):
    """Changement du statut d'une réservation"""
    if current_user.role != 'manager':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Récupérer la réservation actuelle
        reservation = mongo.db.reservations.find_one({'_id': ObjectId(reservation_id)})
        
        if not reservation:
            flash('Réservation non trouvée', 'danger')
            return redirect(url_for('main.gestion_reservations'))

        # Mettre à jour le statut de la réservation
        update_result = mongo.db.reservations.update_one(
            {'_id': ObjectId(reservation_id)},
            {'$set': {
                'status': status,
                'updated_at': datetime.utcnow(),
                'updated_by': current_user.id
            }}
        )
        
        if update_result.modified_count > 0:
            # Gérer la disponibilité de la voiture selon le nouveau statut
            if status == 'acceptee':
                mongo.db.voitures.update_one(
                    {'_id': reservation['voiture_id']},
                    {'$set': {'disponible': False}}
                )
            elif status == 'refusee' or status == 'annulee':
                mongo.db.voitures.update_one(
                    {'_id': reservation['voiture_id']},
                    {'$set': {'disponible': True}}
                )
            
            flash(f'Statut de la réservation mis à jour: {status}', 'success')
        else:
            flash('Aucune modification effectuée', 'warning')
            
    except Exception as e:
        flash(f"Erreur lors de la mise à jour: {str(e)}", 'danger')
    
    return redirect(url_for('main.gestion_reservations'))

@main_bp.route('/annuler_reservation/<reservation_id>')
@login_required
def annuler_reservation(reservation_id):
    try:
        # Vérifier que la réservation existe et appartient à l'utilisateur
        reservation = mongo.db.reservations.find_one({
            '_id': ObjectId(reservation_id),
            '$or': [
                {'created_by': current_user.id},
                {'client_nom': current_user.username}
            ]
        })
        
        if not reservation:
            flash('Réservation non trouvée ou accès non autorisé', 'danger')
            return redirect(url_for('main.gestion_reservations'))

        if reservation['status'] not in ['en_attente', 'acceptee']:
            flash('Cette réservation ne peut plus être annulée', 'warning')
            return redirect(url_for('main.gestion_reservations'))

        # Mettre à jour le statut de la réservation
        update_result = mongo.db.reservations.update_one(
            {'_id': ObjectId(reservation_id)},
            {'$set': {
                'status': 'annulee',
                'updated_at': datetime.utcnow(),
                'updated_by': current_user.id
            }}
        )
        
        if update_result.modified_count > 0:
            # Rendre la voiture disponible
            mongo.db.voitures.update_one(
                {'_id': reservation['voiture_id']},
                {'$set': {'disponible': True}}
            )
            flash('Réservation annulée avec succès', 'success')
        else:
            flash('Aucune modification effectuée', 'warning')
            
    except Exception as e:
        flash(f'Erreur lors de l\'annulation: {str(e)}', 'danger')
    
    return redirect(url_for('main.gestion_reservations'))

# Section Administrateur
@main_bp.route('/admin/gestion_managers')
@login_required
def gestion_managers():
    """Gestion des comptes managers (accès réservé aux administrateurs)"""
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    managers = list(mongo.db.users.find({'role': 'manager'}))
    return render_template('admin/gestion_managers.html', managers=managers)
@main_bp.route('/admin/ajouter_manager', methods=['GET', 'POST'])
@login_required
def ajouter_manager():
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ManagerForm()
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        existing_user = mongo.db.users.find_one({'email': form.email.data})
        if existing_user:
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('main.ajouter_manager'))

        hashed_password = generate_password_hash(form.password.data)
        manager_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password,
            'role': 'manager',
            'created_at': datetime.utcnow(),
            'created_by': ObjectId(current_user.id)  # Convertir en ObjectId
        }
        
        try:
            mongo.db.users.insert_one(manager_data)
            flash('Manager ajouté avec succès!', 'success')
            return redirect(url_for('main.gestion_managers'))
        except Exception as e:
            flash(f"Erreur lors de l'ajout: {str(e)}", 'danger')

    return render_template('admin/ajouter_manager.html', form=form)
@main_bp.route('/admin/modifier_manager/<manager_id>', methods=['GET', 'POST'])
@login_required
def modifier_manager(manager_id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    manager = mongo.db.users.find_one({'_id': ObjectId(manager_id), 'role': 'manager'})
    if not manager:
        flash('Manager non trouvé', 'danger')
        return redirect(url_for('main.gestion_managers'))

    form = ManagerForm()
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà pour un autre utilisateur
        existing_user = mongo.db.users.find_one({
            '_id': {'$ne': ObjectId(manager_id)},
            'email': form.email.data
        })
        if existing_user:
            flash('Cet email est déjà utilisé par un autre utilisateur', 'danger')
            return redirect(url_for('main.modifier_manager', manager_id=manager_id))

        # Préparer les données de mise à jour
        update_data = {
            'username': form.username.data,
            'email': form.email.data,
            'updated_at': datetime.utcnow(),
            'updated_by': current_user.id
        }
        
        # Ajouter le mot de passe uniquement s'il est fourni
        if form.password.data:
            update_data['password'] = generate_password_hash(form.password.data)

        try:
            # Mettre à jour le manager
            result = mongo.db.users.update_one(
                {'_id': ObjectId(manager_id)},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                flash('Manager mis à jour avec succès!', 'success')
            else:
                flash('Aucune modification effectuée', 'info')
            
            return redirect(url_for('main.gestion_managers'))
            
        except Exception as e:
            flash(f"Erreur lors de la mise à jour : {str(e)}", 'danger')
            return redirect(url_for('main.modifier_manager', manager_id=manager_id))

    elif request.method == 'GET':
        # Pré-remplir le formulaire avec les données existantes
        form.username.data = manager.get('username')
        form.email.data = manager.get('email')

    return render_template('admin/modifier_manager.html', form=form, manager=manager)

@main_bp.route('/admin/supprimer_manager/<manager_id>')
@login_required
def supprimer_manager(manager_id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    result = mongo.db.users.delete_one({'_id': ObjectId(manager_id), 'role': 'manager'})
    if result.deleted_count > 0:
        flash('Manager supprimé avec succès', 'success')
    else:
        flash('Manager non trouvé', 'danger')
    return redirect(url_for('main.gestion_managers'))
# Supprimer ou commenter les routes client inutiles
# @main_bp.route('/mes_reservations')
# @main_bp.route('/reserver/<voiture_id>')

# Nouvelle route pour la création manuelle de réservation

    """Création manuelle de réservation par le manager"""
    if current_user.role != 'manager':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ReservationForm()
    
    # Récupérer la liste des clients et voitures disponibles
    clients = list(mongo.db.users.find({'role': 'client'}))
    voitures_dispo = list(mongo.db.voitures.find({'disponible': True}))

    if form.validate_on_submit():
        # Vérifier la disponibilité de la voiture
        voiture = mongo.db.voitures.find_one({'_id': ObjectId(form.voiture_id.data)})
        if not voiture or not voiture.get('disponible'):
            flash('Cette voiture n\'est pas disponible', 'danger')
            return redirect(url_for('main.nouvelle_reservation'))

        reservation_data = {
            'client_id': ObjectId(form.client_id.data),
            'voiture_id': ObjectId(form.voiture_id.data),
            'date_debut': form.date_debut.data,
            'date_fin': form.date_fin.data,
            'status': 'acceptee',  # Directement acceptée par le manager
            'created_by': current_user.id,
            'created_at': datetime.utcnow()
        }

        # Insérer la réservation et marquer la voiture comme indisponible
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.reservations.insert_one(reservation_data, session=session)
                mongo.db.voitures.update_one(
                    {'_id': ObjectId(form.voiture_id.data)},
                    {'$set': {'disponible': False}},
                    session=session
                )

        flash('Réservation créée avec succès!', 'success')
        return redirect(url_for('main.gestion_reservations'))

    return render_template('nouvelle_reservation.html', 
                         form=form,
                         clients=clients,
                         voitures=voitures_dispo)
from datetime import datetime, date  # Ajoutez cet import en haut du fichier




@main_bp.route('/reservation/nouvelle_reservation', methods=['GET', 'POST'])
@login_required
def nouvelle_reservation():
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ReservationForm()
    clients = list(mongo.db.users.find({'role': 'client'}))
    voitures = list(mongo.db.voitures.find({'disponible': True}))

    form.client_id.choices = [(str(c['_id']), f"{c['username']} ({c['email']})") for c in clients]
    form.voiture_id.choices = [(str(v['_id']), f"{v['marque']} {v['modele']}") for v in voitures]

    if form.validate_on_submit():
        # Conversion des dates en datetime
        date_debut = datetime.combine(form.date_debut.data, datetime.min.time())
        date_fin = datetime.combine(form.date_fin.data, datetime.min.time())

        # Calcul du prix total
        jours = (date_fin - date_debut).days
        voiture = mongo.db.voitures.find_one({'_id': ObjectId(form.voiture_id.data)})
        prix_total = jours * voiture['prix']

        reservation_data = {
            'client_id': ObjectId(form.client_id.data),
            'voiture_id': ObjectId(form.voiture_id.data),
            'date_debut': date_debut,
            'date_fin': date_fin,
            'prix_total': prix_total,
            'status': 'acceptee',
            'created_at': datetime.utcnow(),
            'created_by': current_user.id
        }

        # ➡️ Version SANS transaction (simplifiée pour le développement)
        try:
            # 1. Insérer la réservation
            mongo.db.reservations.insert_one(reservation_data)
            
            # 2. Marquer la voiture comme indisponible
            mongo.db.voitures.update_one(
                {'_id': ObjectId(form.voiture_id.data)},
                {'$set': {'disponible': False}}
            )

            flash('Réservation créée avec succès !', 'success')
            return redirect(url_for('reservation/gestion_reservations'))

        except Exception as e:
            flash(f"Erreur lors de la création : {str(e)}", 'danger')
            # Optionnel : logger l'erreur
            print(f"ERREUR: {e}")

    return render_template('reservation/nouvelle_reservation.html', form=form)
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ReservationForm()
    clients = list(mongo.db.users.find({'role': 'client'}))
    voitures = list(mongo.db.voitures.find({'disponible': True}))

    form.client_id.choices = [(str(c['_id']), f"{c['username']} ({c['email']})") for c in clients]
    form.voiture_id.choices = [(str(v['_id']), f"{v['marque']} {v['modele']} - {v['prix']}€/jour") for v in voitures]

    if form.validate_on_submit():
        # Conversion des dates en datetime
        date_debut = datetime.combine(form.date_debut.data, datetime.min.time())
        date_fin = datetime.combine(form.date_fin.data, datetime.min.time())
        
        # Calcul du prix total
        jours = (date_fin - date_debut).days
        voiture = mongo.db.voitures.find_one({'_id': ObjectId(form.voiture_id.data)})
        prix_total = jours * voiture['prix']

        reservation_data = {
            'client_id': ObjectId(form.client_id.data),
            'voiture_id': ObjectId(form.voiture_id.data),
            'date_debut': date_debut,  # Utilisez datetime au lieu de date
            'date_fin': date_fin,      # Utilisez datetime au lieu de date
            'prix_total': prix_total,
            'status': 'acceptee',
            'created_at': datetime.utcnow(),
            'created_by': current_user.id
        }

        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.reservations.insert_one(reservation_data, session=session)
                mongo.db.voitures.update_one(
                    {'_id': ObjectId(form.voiture_id.data)},
                    {'$set': {'disponible': False}},
                    session=session
                )

        flash('Réservation créée avec succès!', 'success')
        return redirect(url_for('main.gestion_reservations'))

    return render_template('nouvelle_reservation.html', 
                         form=form,
                         clients=clients,
                         voitures=voitures)

@main_bp.route('/voiture/<voiture_id>')
def details_voiture(voiture_id):
    """Affiche les détails d'une voiture spécifique"""
    try:
        # Récupérer les informations de la voiture
        voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
        if not voiture:
            flash('Voiture non trouvée', 'danger')
            return redirect(url_for('main.voitures'))
        
        # Récupérer les réservations en cours pour cette voiture
        reservations = list(mongo.db.reservations.find({
            'voiture_id': ObjectId(voiture_id),
            'status': {'$in': ['en_attente', 'acceptee']},
            'date_fin': {'$gte': datetime.now()}
        }).sort('date_debut', 1))
        
        return render_template('voiture/details_voiture.html', 
                            voiture=voiture,
                            reservations=reservations)
    except Exception as e:
        flash(f"Erreur lors de la récupération des détails: {str(e)}", 'danger')
        return redirect(url_for('main.voitures'))

@main_bp.route('/gestion/supprimer_reservation/<reservation_id>')
@login_required
def supprimer_reservation(reservation_id):
    """Suppression d'une réservation"""
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    try:
        # Récupérer la réservation
        reservation = mongo.db.reservations.find_one({'_id': ObjectId(reservation_id)})
        if not reservation:
            flash('Réservation non trouvée', 'danger')
            return redirect(url_for('main.gestion_reservations'))

        # Supprimer la réservation
        result = mongo.db.reservations.delete_one({'_id': ObjectId(reservation_id)})
        
        if result.deleted_count > 0:
            # Rendre la voiture disponible si la réservation était active
            if reservation['status'] in ['en_attente', 'acceptee']:
                mongo.db.voitures.update_one(
                    {'_id': reservation['voiture_id']},
                    {'$set': {'disponible': True}}
                )
            flash('Réservation supprimée avec succès', 'success')
        else:
            flash('Erreur lors de la suppression de la réservation', 'danger')

    except Exception as e:
        flash(f'Erreur : {str(e)}', 'danger')

    return redirect(url_for('main.gestion_reservations'))
