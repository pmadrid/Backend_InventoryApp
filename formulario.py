from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from wtforms.validators import Length

MESSAGE = "Este campo es obligatorio"


class Login(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message=MESSAGE),
                                                   Length(max=30)])
    password = PasswordField('Password', validators=[DataRequired(message=MESSAGE)])
    enviar = SubmitField('Ingresar')
    email = EmailField('Mensaje', validators=[DataRequired(message=MESSAGE)])
    recuperar = SubmitField('Recuperar')
