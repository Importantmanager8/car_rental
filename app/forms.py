from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField 
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import SelectField, BooleanField

from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import DataRequired
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', 
                          validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe',
                            validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class VoitureForm(FlaskForm):
    marque = StringField('Marque', validators=[DataRequired()])
    modele = StringField('Modèle', validators=[DataRequired()])
    annee = StringField('Année', validators=[DataRequired()])
    prix = StringField('Prix par jour', validators=[DataRequired()])
    submit = SubmitField('Ajouter')



class ReservationForm(FlaskForm):
    client_id = SelectField('Client', coerce=str, validators=[DataRequired()])
    voiture_id = SelectField('Voiture', coerce=str, validators=[DataRequired()])
    date_debut = DateField('Date de début', format='%Y-%m-%d', validators=[DataRequired()])
    date_fin = DateField('Date de fin', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Enregistrer')
class ManagerForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[EqualTo('password')])
    submit = SubmitField('Enregistrer')
from wtforms import IntegerField  # Assurez-vous que cet import est présent

class ManagerForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                   validators=[DataRequired(), EqualTo('password')])
    # Correction pour IntegerField:
    annee = IntegerField('Année', validators=[DataRequired()])  # Pas de parenthèses supplémentaires
    submit = SubmitField('Enregistrer')