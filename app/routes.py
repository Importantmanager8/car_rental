import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app import mongo, login_manager
from app.forms import LoginForm, RegistrationForm, VoitureForm, ReservationForm,ManagerForm
from app.models import User
from datetime import datetime
from bson.objectid import ObjectId
from datetime import datetime  # Ajoutez cet import en haut du fichier
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
def index():
    voitures = list(mongo.db.voitures.find({'disponible': True}))
    return render_template('index.html', voitures=voitures)

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
    """Inscription de nouveaux utilisateurs"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
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

@main_bp.route('/voitures')
def voitures():
    """Liste des voitures disponibles"""
    voitures = list(mongo.db.voitures.find({'disponible': True}))
    return render_template('voitures.html', voitures=voitures)

@main_bp.route('/reserver/<voiture_id>', methods=['GET', 'POST'])
@login_required
def reserver(voiture_id):
    voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
    if not voiture:
        flash('Voiture non trouvée', 'danger')
        return redirect(url_for('main.voitures'))
    
    form = ReservationForm()
    
    if form.validate_on_submit():
        # Calcul du nombre de jours
        delta = form.date_fin.data - form.date_debut.data
        jours = delta.days
        total = jours * voiture['prix']
        
        reservation_data = {
            'client_id': current_user.id,
            'voiture_id': ObjectId(voiture_id),
            'date_debut': form.date_debut.data,
            'date_fin': form.date_fin.data,
            'prix_total': total,
            'status': 'en_attente',
            'created_at': datetime.utcnow()
        }
        
        mongo.db.reservations.insert_one(reservation_data)
        flash('Réservation effectuée avec succès!', 'success')
        return redirect(url_for('main.mes_reservations'))
    
    return render_template('reserver.html', form=form, voiture=voiture)
    """Réservation d'une voiture"""
    form = ReservationForm()
    voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
    
    if form.validate_on_submit():
        reservation_data = {
            'client_id': current_user.id,
            'voiture_id': ObjectId(voiture_id),
            'date_debut': form.date_debut.data,
            'date_fin': form.date_fin.data,
            'status': 'en_attente'
        }
        mongo.db.reservations.insert_one(reservation_data)
        flash('Votre réservation a été soumise avec succès!', 'success')
        return redirect(url_for('main.mes_reservations'))
    
    return render_template('reserver.html', form=form, voiture=voiture)


@main_bp.route('/ajouter_voiture', methods=['GET', 'POST'])
@login_required
def ajouter_voiture():
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = VoitureForm()
    if form.validate_on_submit():
        voiture_data = {
            'marque': form.marque.data,
            'modele': form.modele.data,
            'annee': form.annee.data,
            'prix': form.prix.data,
            'disponible': True,
            'created_at': datetime.utcnow()
        }
        mongo.db.voitures.insert_one(voiture_data)
        flash('Voiture ajoutée avec succès!', 'success')
        return redirect(url_for('main.gestion_voitures'))
    
    return render_template('ajouter_voiture.html', form=form)

@main_bp.route('/modifier_voiture/<voiture_id>', methods=['GET', 'POST'])
@login_required
def modifier_voiture(voiture_id):
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    voiture = mongo.db.voitures.find_one({'_id': ObjectId(voiture_id)})
    form = VoitureForm()
    
    if form.validate_on_submit():
        mongo.db.voitures.update_one(
            {'_id': ObjectId(voiture_id)},
            {'$set': {
                'marque': form.marque.data,
                'modele': form.modele.data,
                'annee': form.annee.data,
                'prix': form.prix.data
            }}
        )
        flash('Voiture modifiée avec succès!', 'success')
        return redirect(url_for('main.gestion_voitures'))
    
    elif request.method == 'GET':
        form.marque.data = voiture['marque']
        form.modele.data = voiture['modele']
        form.annee.data = voiture['annee']
        form.prix.data = voiture['prix']
    
    return render_template('modifier_voiture.html', form=form, voiture=voiture)

@main_bp.route('/supprimer_voiture/<voiture_id>')
@login_required
def supprimer_voiture(voiture_id):
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    mongo.db.voitures.delete_one({'_id': ObjectId(voiture_id)})
    flash('Voiture supprimée avec succès', 'success')
    return redirect(url_for('main.gestion_voitures'))

@main_bp.route('/mes_reservations')
@login_required
def mes_reservations():
    """Liste des réservations de l'utilisateur connecté"""
    reservations = list(mongo.db.reservations.find({'client_id': current_user.id}))
    
    # Ajoutez cette ligne pour debug si nécessaire
    print(f"Nombre de réservations trouvées: {len(reservations)}")
    
    return render_template('mes_reservations.html', reservations=reservations)
    """Liste des réservations de l'utilisateur connecté"""
    reservations = list(mongo.db.reservations.find({'client_id': current_user.id}))
    return render_template('mes_reservations.html', reservations=reservations)

# Section Manager
@main_bp.route('/gestion/voitures')
@login_required
def gestion_voitures():
    """Gestion des voitures (accès réservé aux managers)"""
    if current_user.role != 'manager':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    voitures = list(mongo.db.voitures.find())
    return render_template('gestion_voitures.html', voitures=voitures)

@main_bp.route('/gestion/reservations')
@login_required
def gestion_reservations():
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    reservations = list(mongo.db.reservations.find())
    
    # Conversion des ObjectId en strings pour les clés
    clients = {str(client['_id']): client for client in mongo.db.users.find({'role': 'client'})}
    voitures = {str(voiture['_id']): voiture for voiture in mongo.db.voitures.find()}

    return render_template('gestion_reservations.html',
                         reservations=reservations,
                         clients=clients,
                         voitures=voitures)
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    # Récupérer toutes les données nécessaires avant de rendre le template
    reservations = list(mongo.db.reservations.find())
    clients = {str(client['_id']): client for client in mongo.db.users.find({'role': 'client'})}
    voitures = {str(voiture['_id']): voiture for voiture in mongo.db.voitures.find()}

    return render_template('gestion_reservations.html',
                         reservations=reservations,
                         clients=clients,
                         voitures=voitures)
    if current_user.role not in ['manager', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    # Récupération des réservations avec les informations des clients et voitures
    reservations = list(mongo.db.reservations.aggregate([
        {
            '$lookup': {
                'from': 'users',
                'localField': 'client_id',
                'foreignField': '_id',
                'as': 'client'
            }
        },
        {
            '$lookup': {
                'from': 'voitures',
                'localField': 'voiture_id',
                'foreignField': '_id',
                'as': 'voiture'
            }
        },
        {
            '$unwind': '$client'
        },
        {
            '$unwind': {
                'path': '$voiture',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$sort': {'date_debut': -1}
        }
    ]))

    return render_template('gestion_reservations.html', 
                         reservations=reservations)
    """Gestion complète des réservations"""
    if current_user.role != 'manager' and current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    # Gestion du formulaire pour les requêtes POST
    if request.method == 'POST':
        form = ReservationForm()
        if form.validate_on_submit():
            # Vérifier la disponibilité
            voiture = mongo.db.voitures.find_one({'_id': ObjectId(form.voiture_id.data)})
            if not voiture or not voiture.get('disponible'):
                flash('Voiture non disponible', 'danger')
                return redirect(url_for('main.gestion_reservations'))

            # Création de la réservation
            reservation_data = {
                'client_id': ObjectId(form.client_id.data),
                'voiture_id': ObjectId(form.voiture_id.data),
                'date_debut': form.date_debut.data,
                'date_fin': form.date_fin.data,
                'status': 'acceptee',
                'created_by': current_user.id,
                'created_at': datetime.utcnow()
            }

            with mongo.cx.start_session() as session:
                with session.start_transaction():
                    mongo.db.reservations.insert_one(reservation_data, session=session)
                    mongo.db.voitures.update_one(
                        {'_id': ObjectId(form.voiture_id.data)},
                        {'$set': {'disponible': False}},
                        session=session
                    )

            flash('Réservation créée!', 'success')
            return redirect(url_for('main.gestion_reservations'))
    else:
        form = ReservationForm()

    # Récupération des données pour l'affichage
    clients = list(mongo.db.users.find({'role': 'client'}))
    voitures_dispo = list(mongo.db.voitures.find({'disponible': True}))
    
    reservations = list(mongo.db.reservations.aggregate([
        # Votre pipeline d'aggregation existant
    ]))

    return render_template('gestion_reservations.html',
                         form=form,
                         clients=clients,
                         voitures=voitures_dispo,
                         reservations=reservations)

@main_bp.route('/gestion/reservation/<reservation_id>/<status>')
@login_required
def changer_statut_reservation(reservation_id, status):
    """Changement du statut d'une réservation"""
    if current_user.role != 'manager':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            # Mettre à jour le statut de la réservation
            mongo.db.reservations.update_one(
                {'_id': ObjectId(reservation_id)},
                {'$set': {'status': status}},
                session=session
            )
            
            # Si acceptée, marquer la voiture comme indisponible
            if status == 'acceptee':
                reservation = mongo.db.reservations.find_one(
                    {'_id': ObjectId(reservation_id)},
                    session=session
                )
                mongo.db.voitures.update_one(
                    {'_id': reservation['voiture_id']},
                    {'$set': {'disponible': False}},
                    session=session
                )
            # Si refusée et précédemment acceptée, rendre la voiture disponible
            elif status == 'refusee':
                reservation = mongo.db.reservations.find_one(
                    {'_id': ObjectId(reservation_id)},
                    session=session
                )
                if reservation.get('status') == 'acceptee':
                    mongo.db.voitures.update_one(
                        {'_id': reservation['voiture_id']},
                        {'$set': {'disponible': True}},
                        session=session
                    )
    
    flash('Statut de réservation mis à jour', 'success')
    return redirect(url_for('main.gestion_reservations'))
@main_bp.route('/annuler_reservation/<reservation_id>')
@login_required
def annuler_reservation(reservation_id):
    """Annulation d'une réservation par le client"""
    try:
        # Vérification que l'ID est valide
        reservation_oid = ObjectId(reservation_id)
    except:
        flash('ID de réservation invalide', 'danger')
        return redirect(url_for('main.mes_reservations'))

    # Recherche de la réservation avec vérification du propriétaire
    reservation = mongo.db.reservations.find_one({
        '_id': reservation_oid,
        'client_id': current_user.id
    })
    
    if not reservation:
        flash('Réservation non trouvée ou vous n\'y avez pas accès', 'danger')
        return redirect(url_for('main.mes_reservations'))
    
    if reservation.get('status') != 'en_attente':
        flash('Seules les réservations en attente peuvent être annulées', 'warning')
        return redirect(url_for('main.mes_reservations'))
    
    # Transaction pour garantir l'intégrité des données
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            # Suppression de la réservation
            mongo.db.reservations.delete_one(
                {'_id': reservation_oid},
                session=session
            )
            
            # Si la réservation était acceptée, rendre la voiture disponible
            if reservation.get('status') == 'acceptee':
                mongo.db.voitures.update_one(
                    {'_id': reservation['voiture_id']},
                    {'$set': {'disponible': True}},
                    session=session
                )
    
    flash('Réservation annulée avec succès', 'success')
    return redirect(url_for('main.mes_reservations'))
    """Annulation d'une réservation par le client"""
    reservation = mongo.db.reservations.find_one({
        '_id': ObjectId(reservation_id),
        'client_id': current_user.id
    })
    
    if not reservation:
        flash('Réservation non trouvée', 'danger')
        return redirect(url_for('main.mes_reservations'))
    
    if reservation.status != 'en_attente':
        flash('Seules les réservations en attente peuvent être annulées', 'warning')
        return redirect(url_for('main.mes_reservations'))
    
    mongo.db.reservations.delete_one({'_id': ObjectId(reservation_id)})
    flash('Réservation annulée avec succès', 'success')
    return redirect(url_for('main.mes_reservations'))
# Section Administrateur
@main_bp.route('/admin/managers')
@login_required
def gestion_managers():
    """Gestion des comptes managers (accès réservé aux administrateurs)"""
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    managers = list(mongo.db.users.find({'role': 'manager'}))
    return render_template('gestion_managers.html', managers=managers)
@main_bp.route('/admin/ajouter_manager', methods=['GET', 'POST'])
@login_required
def ajouter_manager():
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ManagerForm()
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        if mongo.db.users.find_one({'email': form.email.data}):
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('main.ajouter_manager'))

        hashed_password = generate_password_hash(form.password.data)
        manager_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password,
            'role': 'manager',
            'created_at': datetime.utcnow(),
            'created_by': current_user.id
        }
        mongo.db.users.insert_one(manager_data)
        flash('Manager ajouté avec succès!', 'success')
        return redirect(url_for('main.gestion_managers'))

    return render_template('ajouter_manager.html', form=form)
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    form = ManagerForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        manager_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password,
            'role': 'manager',
            'created_at': datetime.utcnow(),
            'created_by': current_user.id
        }
        mongo.db.users.insert_one(manager_data)
        flash('Manager ajouté avec succès!', 'success')
        return redirect(url_for('main.gestion_managers'))

    return render_template('ajouter_manager.html', form=form)

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
        update_data = {
            'username': form.username.data,
            'email': form.email.data,
            'updated_at': datetime.utcnow()
        }
        if form.password.data:
            update_data['password'] = generate_password_hash(form.password.data)

        mongo.db.users.update_one(
            {'_id': ObjectId(manager_id)},
            {'$set': update_data}
        )
        flash('Manager mis à jour avec succès!', 'success')
        return redirect(url_for('main.gestion_managers'))

    elif request.method == 'GET':
        form.username.data = manager.get('username')
        form.email.data = manager.get('email')

    return render_template('modifier_manager.html', form=form, manager=manager)

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

@main_bp.route('/nouvelle_reservation', methods=['GET', 'POST'])
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
            return redirect(url_for('main.gestion_reservations'))

        except Exception as e:
            flash(f"Erreur lors de la création : {str(e)}", 'danger')
            # Optionnel : logger l'erreur
            print(f"ERREUR: {e}")

    return render_template('nouvelle_reservation.html', form=form)
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
