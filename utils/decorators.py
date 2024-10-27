# utils/decorators.py
from functools import wraps
from flask import request, jsonify
import jwt
from config import config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        data = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        if not data.get('admin'):
            return jsonify({'message': 'Admin access required!'}), 403
        return f(*args, **kwargs)
    return decorated
