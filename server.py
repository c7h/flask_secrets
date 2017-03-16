import os
import re
from uuid import uuid4

from flask import Flask, url_for, g, jsonify
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.mail import Mail, Message
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context

from errors import (
	errors,
	ParameterException,
	RessourceExistsException,
	NotFoundException,
)

app = Flask(__name__)
api = Api(app, catch_all_404s=True, errors=errors)
mail = Mail(app)
auth = HTTPBasicAuth()

# configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:////tmp/database.db')
db = SQLAlchemy(app)


## Models

class User(db.Model):
	"""
	The user model stores user password hashed and
	validation information. A user needs to validate after creation.
	"""
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(16), index=True)
	password_hash = db.Column(db.String(128))

	# user validation information
	validated = db.Column(db.Boolean, default=False)
	validation_token = db.Column(db.String(32), default=uuid4().hex)

	def hash_password(self, password):
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	def __repr__(self):
		return '<User %s>' % self.username


class Secret(db.Model):
	"""
	The secret model stores generic secret messages.
	"""
	__tablename__ = 'secrets'
	id = db.Column(db.Integer, primary_key=True)
	secret = db.Column(db.UnicodeText)
	created_by = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

	@property
	def serialize(self):
		return {
			"id": self.id,
			"secret": self.secret,
			"created_by": User.query.filter_by(id=self.created_by).first().username
		}


class UserListRessource(Resource):
	"""simple user list ressource at /users/"""

	parser = reqparse.RequestParser()
	parser.add_argument('username', type=str, help="users login name")
	parser.add_argument('password', type=str, help="users password")

	def post(self):
		"""generate new user"""
		# check if user already exists:

		args = self.parser.parse_args()
		username = args.get('username')
		password = args.get('password')

		if not (username and password):
			raise ParameterException("provide username and password")

		# check if username is an email address
		if not re.match(r'([\w\.]+)@([\w\.]+)\.(\w+)', username):
			raise ParameterException("username must be email address")

		# check if username already exists:
		if User.query.filter_by(username=username).first():
			raise RessourceExistsException()

		# create user
		user = User(username=username)
		user.hash_password(password)
		db.session.add(user)
		# we need to commit to db here, because further steps rely on user.id
		db.session.commit()

		# send validation email
		validation_url = url_for(
			'uservalidation',
			user_id=user.id,
			validation_code=user.validation_token,
		)

		print(validation_url)
		validation_mail = Message(
			"please validate your account by opening this url: %s" % validation_url,
			recipients=user.username,
			sender=('Super Secret App', 'secretapp@gerneth.info')
		)

		try:
			mail.send(validation_mail)
		except Exception as e:
			# remove user from database
			db.session.delete(user)
			db.session.commit()
			raise e

		return {"result": "ok",
				"id": user.id}, 201


class UserResource(Resource):
	"""
	# users object at /users/<user_id>
	"""

	@auth.login_required
	def get(self, user_id):
		"""
		Show details for user. You need to be logged in for that
		:param user_id: id of the user
		:return: 200
		"""

		user = User.query.filter_by(id=user_id).first()

		if not user:
			raise NotFoundException

		return {"id": user.id,
				"name": user.username}, 200


class UserValidation(Resource):
	"""This is a sub-resource of a user."""

	def post(self, user_id, validation_code):
		# we forward post and get to patch
		# to make the resource more robust
		self.patch(user_id, validation_code)

	def get(self, user_id, validation_code):
		self.patch(user_id, validation_code)

	def patch(self, user_id, validation_token):
		"""
		Validate a user. Check if validation code
		matches the one created on registration and update
		record in database.
		:param user_id: id of the user
		:param validation_token: token used for validation
		:return:
		"""
		user = User.query.get(user_id)
		if not user:
			# user id doest not exist in db
			raise NotFoundException

		# validate code
		if user.validation_token == validation_token:
			# matching - validate user
			user.validated = True
			db.session.commit()
			return {"result": "ok"}, 200
		else:
			# validation code does not match
			raise ValueError


class SecretsListResource(Resource):
	parser = reqparse.RequestParser()
	parser.add_argument("secret", type=str, help="super secret message")

	@auth.login_required
	def get(self):
		"""get list of secrets"""
		return jsonify(secrets=[i.serialize for i in Secret.query.all()])

	@auth.login_required
	def post(self):
		"""
		create a new secret
		:return: 201 on success
		"""
		args = self.parser.parse_args()
		secret = args.get('secret')

		new_secret = Secret(secret=secret)
		new_secret.created_by = g.user.id
		db.session.add(new_secret)
		db.session.commit()

		return {"result": "ok",
				"id": new_secret.id}, 201


@auth.verify_password
def verify_password(username, password):
	"""
	used by the httpauth module to validate passwords for users.
	Only authenticated users can login.
	:param username: username to check
	:param password: password to validate
	:return: True, if correct
	"""
	user = User.query.filter_by(username=username).first()
	if not user or not user.verify_password(password):
		return False
	g.user = user
	return user.validated


# register endpoints
api.add_resource(UserListRessource, '/users')
api.add_resource(UserResource, '/users/<int:user_id>')
api.add_resource(UserValidation, '/users/<int:user_id>/validation/<string:validation_code>')
api.add_resource(SecretsListResource, '/secrets')
