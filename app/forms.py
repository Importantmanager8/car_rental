from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, SubmitField, DateField, BooleanField,
    TextAreaField, IntegerField, SelectField, SelectMultipleField, FloatField, DecimalField, MultipleFileField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from wtforms.widgets import ListWidget, CheckboxInput
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', 
                         validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class VoitureForm(FlaskForm):
    marque = StringField('Marque', validators=[DataRequired()])
    modele = StringField('Modèle', validators=[DataRequired()])
    annee = IntegerField('Année', validators=[DataRequired()])
    prix = DecimalField('Prix par jour', validators=[DataRequired()])
    description = TextAreaField('Description')
    options = TextAreaField('Options (une par ligne)')
    disponible = BooleanField('Disponible')
    images = MultipleFileField('Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement!')
    ])
    image_principale = SelectField('Image Principale', choices=[], validators=[Optional()])
    submit = SubmitField('Enregistrer')

class ReservationForm(FlaskForm):
    # REMPLACEZ TOUT LE CONTENU EXISTANT PAR :
    client_nom = StringField('Nom complet', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    voiture_id = SelectField('Voiture', choices=[], validators=[DataRequired()])
    date_debut = DateField('Date début', format='%Y-%m-%d', validators=[DataRequired()])
    date_fin = DateField('Date fin', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Réserver')

    # Cette méthode est cruciale pour rafraîchir les choix
    def refresh_voitures(self, voitures):
        self.voiture_id.choices = [
            (str(v['_id']), f"{v['marque']} {v['modele']} - {v['prix']}€/jour")
            for v in voitures
        ]
class ManagerForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=2, max=20)
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(), 
        EqualTo('password')
    ])
    submit = SubmitField('Ajouter Manager')