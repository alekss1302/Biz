# blueprints/reviews.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.decorators import token_required
from utils.db import db

reviews_blueprint = Blueprint('reviews', __name__)

@reviews_blueprint.route('/<string:business_id>', methods=['POST'])
@token_required
def add_review(business_id):
    review = {
        '_id': ObjectId(),
        'username': request.form['username'],
        'comment': request.form['comment'],
        'stars': int(request.form['stars'])
    }
    db['biz'].update_one({'_id': ObjectId(business_id)}, {'$push': {'reviews': review}})
    return jsonify({'message': 'Review added!'}), 201
