"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/
This file creates your application.
"""

import os
from app import app, db
from flask import render_template, request, redirect, jsonify, url_for, flash, session, send_from_directory
from app.models import *
from .forms import *
from werkzeug.utils import secure_filename

from flask_login import current_user, login_user, logout_user

import jwt
from flask import _request_ctx_stack
from functools import wraps



def login_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.headers.get('Authorization', None)
		if not auth:
			return jsonify({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'}), 401

		parts = auth.split()

		if parts[0].lower() != 'bearer':
			return jsonify({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}), 401
		elif len(parts) == 1:
			return jsonify({'code': 'invalid_header', 'description': 'Token not found'}), 401
		elif len(parts) > 2:
			return jsonify({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}), 401

		token = parts[1]
		try:
				payload = jwt.decode(token, app.config['SECRET_KEY'])

		except jwt.ExpiredSignature:
			return jsonify({'code': 'token_expired', 'description': 'token is expired'}), 401
		except jwt.DecodeError:
			return jsonify({'code': 'token_invalid_signature', 'description': 'Token signature is invalid'}), 401

		return f(*args, **kwargs)

	return decorated


###
# Routing for your application.
###

# -------------------------------------------------------------------------------
# LOGIN, LOGOUT & SIGNUP SECTION
# -------------------------------------------------------------------------------
@app.route('/api/register', methods=['POST'])
def register():

	form = RegisterForm()

	if request.method=='POST' and form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		fullname = form.fullname.data
		email = form.email.data
		location = form.location.data
		biography = form.biography.data  
		photo = form.photo.data

		filename=secure_filename(photo.filename)
		photo.save(os.path.join(app.config['USER_UPLOAD_FOLDER'], filename))
		
		data = Users(username, password, fullname, location, email, biography, filename)

		db.session.add(data)
		db.session.commit()

		register = {
			"status": 200,
			"message": fullname + ", Registered Successfully",
			"username": username
		}

		return jsonify(register=register)
	#  return jsonify(errorMsg(form))


@app.route('/api/auth/login', methods=['POST'])
def login():

	form = LoginForm()

	if request.method == "POST" and form.validate_on_submit():

		username = form.username.data
		user_password = form.password.data

		user = Users.query.filter_by(username=username).first()
		# print(user, user.check_password(user_password))

		if (user is None) or (not user.check_password(user_password)):
			return jsonify({"message": "Username or Password Incorrect"}), 500

		token = jwt.encode({'id': user.id, 'username':username}, app.config['SECRET_KEY'], algorithm='HS256')#.decode('utf-8')
		session['userid'] = user.id

		return jsonify({'token': token, 'message': 'User successfully logged in!', 'id':user.id}), 200

	return jsonify(error=form_errors(form)), 200


@app.route('/api/auth/logout')
@login_required
def logout():

	logout_user()

	return jsonify({"message": "User successfully logged out"}),200


# -------------------------------------------------------------------------------
# USER SECTION
# -------------------------------------------------------------------------------
@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):

	# Retrieves a User from the Database with the matching User ID
	user = db.session.query(Users).filter(Users.id == user_id).first()

	print('User', user)
	#TODO: Might want to check if the User was actually found
	user_details = {
		"id": user.id,
		"username": user.username,
		"name": user.name,
		"photo": user.photo,
		"email": user.email,
		"location": user.location,
		"biography": user.biography,
		"date_joined": user.date_joined
	}

	return jsonify(user_details), 200


@app.route('/api/users/<user_id>/favourites', methods=['GET'])
def get_favourites(user_id):

	# Gets all the cars favourited by the 'current' user
	favourites = db.session.query(CarsModel).join(Favourites).filter(Favourites.user_id == user_id).all()
	
	fav_cars = [] # Stores all the cars as JSON objects

	# Adds all JSON Car-objects to the list
	for fav_car in favourites:
		car = {
			"id": fav_car.id,
			"description": fav_car.description,
			"year": fav_car.year,
			"make": fav_car.make,
			"model": fav_car.model,
			"colour": fav_car.colour,
			"transmission": fav_car.transmission,
			"car_type": fav_car.car_type,
			"price": fav_car.price,
			"photo": fav_car.photo,
			"user_id": fav_car.user_id
		}
		fav_cars.append(car)

	return jsonify(fav_cars), 200


# -------------------------------------------------------------------------------
# CAR DETAILS SECTION
# -------------------------------------------------------------------------------
@app.route('/api/cars/<car_id>', methods=['GET'])
def get_car(car_id):
	"""
		Get Details of a specific car.
	"""

	# Convert to integer - just in case
	car_id = int(car_id)

	# Retrieves a Car from the Database with the matching Car ID
	requested_car = db.session.query(CarsModel).filter_by(id=car_id).first()
	# OR - (either should work) | requested_car = db.session.query(CarsModel).get(car_id)

	# Check to see if the Car was found
	if (requested_car == None):

		error_message = {
			"message": "Access token is missing or invalid"
		}

		# If Car not found, send 401 & error message
		return jsonify(error_message), 401

	# Create new car object
	car = {
		"id": requested_car.id,
		"description": requested_car.description,
		"year": requested_car.year,
		"make": requested_car.make,
		"model": requested_car.model,
		"colour": requested_car.colour,
		"transmission": requested_car.transmission,
		"car_type": requested_car.car_type,
		"price": requested_car.price,
		"photo": requested_car.photo,
		"user_id": requested_car.user_id
	}

	# Gets the User's ID to make a Fasvourite's object
	# current_user_id = current_user.id
	current_user_id = 2 #TODO: Find a way to get the current User ID

	# Retrieves a Favourite from the Database with the matching Car ID
	requested_fav = db.session.query(Favourites).filter_by(car_id=car_id, user_id=current_user_id).first()

	# Check to see if the Favourite was found for that Car and User
	if (requested_fav != None):
		# If found, send 201. It's not an error, but it should identify when a car was favourited
		return jsonify(car), 201

	return jsonify(car), 200


@app.route('/api/cars/<car_id>/favourite', methods=['POST'])
# @login_required
def favourite_car(car_id):
	"""
		Add car to Favourites for logged in user.
	"""

	# Gets the User's ID to make a Fasvourite's object
	# current_user_id = current_user.id
	current_user_id = 2 #TODO: Find a way to get the current User ID

	# Retrieves a Favourite from the Database with the matching Car ID
	requested_fav = db.session.query(Favourites).filter_by(car_id=car_id, user_id=current_user_id).first()

	# Created the Favourite JSON object
	favourite_obj = {
		"message": "Car Successfully Favourited",
		"car_id": car_id
	}

	# Check to see if the Favourite was found
	if (requested_fav != None):
		
		favourite_obj = {
			"message": "Access token is missing or invalid",
			"car_id": car_id
		}

		# If found, delete it from the database
		db.session.delete(requested_fav)
		db.session.commit()

		return jsonify(favourite_obj), 401

	# Make Favourite's object for database...
	favourite = Favourites(car_id, current_user_id)

	# ... then add it to the database
	db.session.add(favourite)
	db.session.commit()

	# flash('Added to Favourite!', category='success')
	return jsonify(favourite_obj), 200


# This is needed to retrieve the images from the uploads folder
@app.route('/uploads/<filename>')
def get_image(filename):
	rootdir = os.getcwd()
	return send_from_directory(os.path.join(rootdir, app.config['UPLOAD_FOLDER']), filename)


# -------------------------------------------------------------------------------
# ADD CAR SECTION
# -------------------------------------------------------------------------------


# -------------------------------------------------------------------------------
# SEARCH CAR SECTION
# -------------------------------------------------------------------------------
@app.route('/api/search', methods=['GET'])
def search():
	
	make = "Honda"
	model = " "
	make_search = "%{}%".format(make)
	model_search = "%{}%".format(model)

	# Gets all the cars with matching 'make' and 'model'
	matching_cars = db.session.query(CarsModel).filter(CarsModel.make.like(make_search)).all()
	
	all_cars = [] # Stores all the cars as JSON objects

	# Adds all JSON Car-objects to the list
	for matched_car in matching_cars:
		car = {
			"id": matched_car.id,
			"description": matched_car.description,
			"year": matched_car.year,
			"make": matched_car.make,
			"model": matched_car.model,
			"colour": matched_car.colour,
			"transmission": matched_car.transmission,
			"car_type": matched_car.car_type,
			"price": matched_car.price,
			"photo": matched_car.photo,
			"user_id": matched_car.user_id
		}

		all_cars.append(car)

	return jsonify(all_cars), 200


# -------------------------------------------------------------------------------
# ALL other routes should be defined above
# -------------------------------------------------------------------------------


"""
	Please create all new routes and views functions above this route.
	This route is now our catch all route for our VueJS single page application.
"""
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
	"""
	Because we use HTML5 history mode in vue-router we need to configure our
	web server to redirect all routes to index.html. Hence the additional route
	"/<path:path".

	Also we will render the initial webpage and then let VueJS take control.
	"""
	# return app.send_static_file('index.html')
	return render_template('index.html')

"""
	Here we defined a function to collect form errors from Flask-WTF which we can use later.
"""
def form_errors(form): # TODO: Rename according to python standards
	error_messages = [] # TODO: Rename according to python standards
   
	for field, errors in form.errors.items():
		for error in errors:
			message = u"You have an error in %s field, %s" % (getattr(form, field).label.text, error)
			error_messages.append(message)

	return error_messages

###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
	"""Send your static text file."""
	file_dot_text = file_name + '.txt'
	return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
	"""
	Add headers to both force latest IE rendering engine or Chrome Frame,
	and also tell the browser not to cache the rendered page. If we wanted
	to we could change max-age to 600 seconds which would be 10 minutes.
	"""
	response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	response.headers['Cache-Control'] = 'public, max-age=0'
	return response


@app.errorhandler(404)
def page_not_found(error):
	"""Custom 404 page."""
	return render_template('404.html'), 404
