# blueprints/auth.py
from flask import Blueprint, request, jsonify
from utils.decorators import token_required
import bcrypt
import jwt
from datetime import datetime, timedelta
from config import config
from utils.db import db

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    db['users'].insert_one({'username': data['username'], 'password': hashed_password})
    return jsonify({'message': 'User registered successfully!'})

@auth_blueprint.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    user = db['users'].find_one({'username': auth.username})
    if user and bcrypt.checkpw(auth.password.encode('utf-8'), user['password']):
        token = jwt.encode({'username': user['username'], 'exp': datetime.utcnow() + timedelta(hours=1)}, config.SECRET_KEY)
        return jsonify({'token': token})
    return jsonify({'message': 'Login failed!'}), 401
