from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import bcrypt

import jwt
import datetime
from functools import wraps

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["bizDB"]      # select the database
users_collection = db['biz']
app.config['SECRET_KEY'] = 'mysecret'
blacklist_collection = db['blacklist']


# application functionality will go here

import random, json

# Function to generate dummy data for businesses
def generate_dummy_data():
    towns = ['Coleraine', 'Banbridge', 'Belfast', 'Lisburn', 'Ballymena', 
             'Derry', 'Newry', 'Enniskillen', 'Omagh', 'Ballymoney']
    
    business_list = []  # List to hold business dictionaries
    
    for i in range(100):
        name = "Biz " + str(i)  # Business name, e.g., "Biz 0"
        town = towns[random.randint(0, len(towns)-1)]  # Randomly select a town
        rating = random.randint(1, 5)  # Assign a random rating between 1 and 5
        
        # Create a dictionary for each business and append to the list
        business_list.append({
            "name": name,
            "town": town,
            "rating": rating,
            "reviews": []  # Empty list to hold reviews later
        })
    
    return business_list

# Generate dummy data and save it as a JSON file
businesses = generate_dummy_data()
with open("data.json", "w") as fout:
    fout.write(json.dumps(businesses))  # Write the data to data.json


from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId  # Required to handle MongoDB ObjectId type

app = Flask(__name__)

# Establish a connection to the MongoDB server (localhost)
client = MongoClient("mongodb://127.0.0.1:27017")

# Select the database and collection
db = client.bizDB  # Select database "bizDB"
businesses = db.biz  # Select collection "biz"

# Endpoint to get all businesses (with optional pagination)
@app.route("/api/v1.0/businesses", methods=["GET"])
def show_all_businesses():
    # Default pagination values
    page_num, page_size = 1, 10
    
    # Get 'pn' (page number) and 'ps' (page size) from query parameters, if available
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    
    page_start = (page_size * (page_num - 1))  # Calculate the start index
    
    data_to_return = []  # List to hold businesses to return
    
    # Find businesses and apply pagination (skip and limit)
    for business in businesses.find().skip(page_start).limit(page_size):
        business['_id'] = str(business['_id'])  # Convert ObjectId to string for JSON serialization
        for review in business['reviews']:
            review['_id'] = str(review['_id'])  # Convert ObjectId in reviews
        data_to_return.append(business)
    
    return make_response(jsonify(data_to_return), 200)

# Endpoint to get a specific business by ID
@app.route("/api/v1.0/businesses/<string:id>", methods=["GET"])
def show_one_business(id):
    try:
        # Find the business by its ObjectId
        business = businesses.find_one({'_id': ObjectId(id)})
        if business:
            business['_id'] = str(business['_id'])  # Convert ObjectId for JSON response
            for review in business['reviews']:
                review['_id'] = str(review['_id'])  # Convert ObjectId in reviews
            return make_response(jsonify(business), 200)
        else:
            return make_response(jsonify({"error": "Business not found"}), 404)
    except Exception:
        return make_response(jsonify({"error": "Invalid business ID"}), 400)

# Endpoint to add a new business
@app.route("/api/v1.0/businesses", methods=["POST"])
def add_business():
    # Check if required fields are present in the request
    if "name" in request.form and "town" in request.form and "rating" in request.form:
        new_business = {
            "name": request.form["name"],
            "town": request.form["town"],
            "rating": int(request.form["rating"]),
            "reviews": []  # Start with an empty list of reviews
        }
        
        # Insert the new business into the collection
        new_business_id = businesses.insert_one(new_business)
        new_business_link = f"http://localhost:5000/api/v1.0/businesses/{new_business_id.inserted_id}"
        
        return make_response(jsonify({"url": new_business_link}), 201)  # Return the URL of the new business
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)

# Endpoint to update a business by ID
@app.route("/api/v1.0/businesses/<string:id>", methods=["PUT"])
def edit_business(id):
    # Check if required fields are present in the request
    if "name" in request.form and "town" in request.form and "rating" in request.form:
        result = businesses.update_one(
            {"_id": ObjectId(id)},  # Find the business by ObjectId
            {"$set": {
                "name": request.form["name"],
                "town": request.form["town"],
                "rating": int(request.form["rating"])
            }}
        )
        
        # Check if any document was updated
        if result.matched_count == 1:
            edited_business_link = f"http://localhost:5000/api/v1.0/businesses/{id}"
            return make_response(jsonify({"url": edited_business_link}), 200)
        else:
            return make_response(jsonify({"error": "Business not found"}), 404)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 400)

# Endpoint to delete a business by ID
@app.route("/api/v1.0/businesses/<string:id>", methods=["DELETE"])
def delete_business(id):
    result = businesses.delete_one({"_id": ObjectId(id)})  # Find and delete the business by ObjectId
    
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)  # No content to return, but deletion successful
    else:
        return make_response(jsonify({"error": "Business not found"}), 404)

# Sub-document (reviews) operations: Add a review
@app.route("/api/v1.0/businesses/<string:id>/reviews", methods=["POST"])
def add_new_review(id):
    new_review = {
        "_id": ObjectId(),  # Generate a unique ObjectId for the review
        "username": request.form["username"],
        "comment": request.form["comment"],
        "stars": int(request.form["stars"])
    }
    
    # Add the new review to the business's reviews array
    businesses.update_one({"_id": ObjectId(id)}, {"$push": {"reviews": new_review}})
    
    new_review_link = f"http://localhost:5000/api/v1.0/businesses/{id}/reviews/{new_review['_id']}"
    return make_response(jsonify({"url": new_review_link}), 201)



@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
    
    # Fetch user from the database and verify password
    user = users_collection.find_one({'username': auth.username})
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # Verify password using bcrypt
    if bcrypt.checkpw(auth.password.encode('utf-8'), user['password']):
        # Generate JWT token
        token = jwt.encode({
            'user': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token.decode('UTF-8')})
    
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        return f(*args, **kwargs)
    return decorated


@app.route('/businesses', methods=['GET'])
@token_required
def get_businesses():
    businesses = db['businesses'].find()  # Assuming you have a businesses collection
    output = []
    for business in businesses:
        output.append({'name': business['name'], 'rating': business['rating']})
    
    return jsonify({'businesses': output})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    users_collection.insert_one({
        'username': data['username'],
        'password': hashed_password,
        'admin': False  # Or True for admin users
    })

    return jsonify({'message': 'User registered successfully!'})


@app.route('/logout', methods=['GET'])
@token_required
def logout():
    token = request.headers.get('x-access-token')
    blacklist_collection.insert_one({'token': token})
    return jsonify({'message': 'Logout successful!'})


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        if blacklist_collection.find_one({'token': token}):
            return jsonify({'message': 'Token has been blacklisted!'}), 403
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        if not data['admin']:
            return jsonify({'message': 'Admin access required!'}), 403
        return f(*args, **kwargs)
    return decorated


@app.route('/businesses/<id>', methods=['DELETE'])
@token_required
@admin_required
def remove_business(id):
    db['businesses'].delete_one({'_id': id})
    return jsonify({'message': 'Business deleted!'})



if __name__ == "__main__":
    app.run(debug=True)  # Start the Flask application

