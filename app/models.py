from . import db
from datetime import datetime
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class CarsModel(db.Model):
    id = db.Column(db.Integer, primary_key=True,  autoincrement=True)
    description = db.Column(db.String(255))
    make = db.Column(db.String(160))
    model = db.Column(db.String(160))
    colour = db.Column(db.String(160))
    year = db.Column(db.String(160))
    transmission = db.Column(db.String(160))
    car_type = db.Column(db.String(160))
    price = db.Column(db.Float, nullable=False)
    photo = db.Column(db.String(160))
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='SET NULL'))

    on_sale_car = db.relationship('Users', back_populates="seller")
    liked_car = db.relationship('Favourites', back_populates="liked_car")

    def __init__(self, description, make, model, color, year, transmission, car_type, price, photo, user_id):
        self.description = description
        self.make = make
        self.model = model
        self.colour = color
        self.year = year
        self.transmission = transmission
        self.car_type = car_type
        self.price = price
        self.photo = photo
        self.user_id = user_id

    def __repr__(self):
        return '<CarsModel %r>' % (self.id)


class Favourites(db.Model):
    id = db.Column(db.Integer, primary_key=True,  autoincrement=True)
    car_id = db.Column(db.Integer, db.ForeignKey(
        'cars_model.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='CASCADE'))

    liked_car = db.relationship(
        'CarsModel', back_populates="liked_car", passive_deletes=True)
    user_liked = db.relationship(
        'Users', back_populates="user_liked", passive_deletes=True)

    def __init__(self, car_id, user_id):
        self.car_id = car_id
        self.user_id = user_id

    def __repr__(self):
        return '<Favourites %r>' % (self.id)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True,  autoincrement=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))
    location = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    biography = db.Column(db.String(255))
    photo = db.Column(db.String(255))
    date_joined = db.Column(db.DateTime, server_default=func.now())

    user_liked = db.relationship('Favourites', back_populates="user_liked")
    seller = db.relationship('CarsModel', back_populates="on_sale_car")

    def __init__(self, username, password, name, location, email, biography, photo):
        self.username = username
        self.password = generate_password_hash(password)
        self.name = name
        self.location = location
        self.email = email
        self.biography = biography
        self.photo = photo

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def check_password(self, password):
    	return check_password_hash(self.password, password)

    def get_id(self):
        try:
            return unicode(self.id)  # python 2 support
        except NameError:
            return str(self.id)  # python 3 support

    def __repr__(self):
        return '<Users %r>' % (self.id)
