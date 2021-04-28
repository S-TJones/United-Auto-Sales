from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, TextField, FileField
from wtforms.validators import InputRequired,DataRequired
from flask_wtf.csrf import CSRFProtect
from app import app
from flask_wtf.file import FileField, FileRequired, FileAllowed

class RegisterForm(FlaskForm):
    csrf = CSRFProtect(app)
    username = TextField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    fullname = TextField('Fullname', validators=[DataRequired()])
    email = TextField('Email', validators=[DataRequired()])
    location = TextField('Location', validators=[DataRequired()])
    biography =TextAreaField('Biography', validators=[DataRequired()])
    photo = FileField('Photo', validators=[FileRequired(), FileAllowed(['jpg','png'])])

class LoginForm(FlaskForm):
    csrf = CSRFProtect(app)
    username = TextField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class SearchForm(FlaskForm):
    make = TextField('Make',validators=[DataRequired()])  
    model = TextField('Model',validators=[DataRequired()])