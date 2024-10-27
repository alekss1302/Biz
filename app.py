from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import jwt
import datetime
import random, json
from functools import wraps

from blueprints.auth import auth_blueprint
from blueprints.business import business_blueprint
from blueprints.reviews import reviews_blueprint
from config import config

app = Flask(__name__)

# Database setup
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["bizDB"]
users_collection = db['users']
businesses_collection = db['biz']
blacklist_collection = db['blacklist']
app.config.from_object(config)

# Register Blueprints
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(business_blueprint, url_prefix='/businesses')
app.register_blueprint(reviews_blueprint, url_prefix='/reviews')

# Generate dummy business data
def generate_dummy_data():
    towns = ['Coleraine', 'Banbridge', 'Belfast', 'Lisburn', 'Ballymena', 
             'Derry', 'Newry', 'Enniskillen', 'Omagh', 'Ballymoney']
    
    business_list = []
    for i in range(100):
        business_list.append({
            "name": f"Biz {i}",
            "town": random.choice(towns),
            "rating": random.randint(1, 5),
            "reviews": []
        })
    return business_list

businesses = generate_dummy_data()
with open("data.json", "w") as fout:
    fout.write(json.dumps(businesses))

# JWT Decorators
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        if blacklist_collection.find_one({'token': token}):
            return jsonify({'message': 'Token has been blacklisted!'}), 403
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        if not data.get('admin'):
            return jsonify({'message': 'Admin access required!'}), 403
        return f(*args, **kwargs)
    return decorated

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        'username': data['username'],
        'password': hashed_password,
        'admin': data.get('admin', False)
    })
    return jsonify({'message': 'User registered successfully!'})

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
    user = users_collection.find_one({'username': auth.username})
    if not user or not bcrypt.checkpw(auth.password.encode('utf-8'), user['password']):
        return jsonify({'message': 'Login failed'}), 401
    token = jwt.encode({
        'user': user['username'],
        'admin': user.get('admin', False),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token': token})

@app.route('/logout', methods=['GET'])
@token_required
def logout():
    token = request.headers.get('x-access-token')
    blacklist_collection.insert_one({'token': token})
    return jsonify({'message': 'Logout successful!'})

# Business Routes
@app.route('/api/v1.0/businesses', methods=['GET'])
@token_required
def show_all_businesses():
    page_num = int(request.args.get('pn', 1))
    page_size = int(request.args.get('ps', 10))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    for business in businesses_collection.find().skip(page_start).limit(page_size):
        # Convert ObjectId to string in the main document
        business['_id'] = str(business['_id'])
        
        # If there are nested ObjectIds (like in reviews), convert those as well
        if 'reviews' in business:
            for review in business['reviews']:
                review['_id'] = str(review['_id'])
        
        data_to_return.append(business)
    
    return jsonify(data_to_return)



@app.route("/api/v1.0/businesses/<string:id>", methods=["GET"])
@token_required
def show_one_business(id):
    try:
        business = businesses_collection.find_one({'_id': ObjectId(id)})
        if not business:
            return jsonify({"error": "Business not found"}), 404
        business['_id'] = str(business['_id'])
        return jsonify(business)
    except:
        return jsonify({"error": "Invalid business ID"}), 400

@app.route("/api/v1.0/businesses", methods=["POST"])
@token_required
def add_business():
    data = request.form
    if all(k in data for k in ("name", "town", "rating")):
        new_business = {
            "name": data["name"],
            "town": data["town"],
            "rating": int(data["rating"]),
            "reviews": []
        }
        new_business_id = businesses_collection.insert_one(new_business).inserted_id
        return jsonify({"url": f"http://localhost:5000/api/v1.0/businesses/{new_business_id}"}), 201
    return jsonify({"error": "Missing form data"}), 400

@app.route("/api/v1.0/businesses/<string:id>", methods=["PUT"])
@token_required
@admin_required
def edit_business(id):
    data = request.form
    if all(k in data for k in ("name", "town", "rating")):
        result = businesses_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"name": data["name"], "town": data["town"], "rating": int(data["rating"])}}
        )
        if result.matched_count:
            return jsonify({"message": "Business updated successfully"}), 200
        return jsonify({"error": "Business not found"}), 404
    return jsonify({"error": "Missing form data"}), 400

@app.route("/api/v1.0/businesses/<string:id>", methods=["DELETE"])
@token_required
@admin_required
def delete_business(id):
    result = businesses_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count:
        return jsonify({'message': 'Business deleted!'}), 204
    return jsonify({"error": "Business not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
