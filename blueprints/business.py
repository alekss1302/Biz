# blueprints/business.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.decorators import token_required, admin_required
from utils.db import db

business_blueprint = Blueprint('business', __name__)

@business_blueprint.route('/', methods=['GET'])
@token_required
def get_all_businesses():
    businesses = db['biz'].find()
    return jsonify([{**biz, '_id': str(biz['_id'])} for biz in businesses])

@business_blueprint.route('/<string:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_business(id):
    result = db['biz'].delete_one({'_id': ObjectId(id)})
    if result.deleted_count:
        return jsonify({'message': 'Business deleted!'}), 204
    return jsonify({'error': 'Business not found'}), 404
