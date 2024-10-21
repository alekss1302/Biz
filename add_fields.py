from pymongo import MongoClient
import random

# Connect to the local MongoDB server
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB  # Select the 'bizDB' database
businesses = db.biz  # Select the 'biz' collection

# Loop through each business in the collection
for business in businesses.find():
    # Add fields for number of employees and profits for 2022-2024
    businesses.update_one(
        {"_id": business['_id']},  # Match the business by its ObjectId
        {
            "$set": {
                "num_employees": random.randint(1, 100),  # Random employees (1-100)
                "profit": [
                    {"year": "2022", "gross": random.randint(-500000, 500000)},  # Random profit
                    {"year": "2023", "gross": random.randint(-500000, 500000)},
                    {"year": "2024", "gross": random.randint(-500000, 500000)}
                ]
            }
        }
    )

# Removing a field by specifying $unset
for business in businesses.find():
    businesses.update_one(
        {"_id": business['_id']},  # Match by ObjectId
        {"$unset": {"dummy": ""}}  # Remove the 'dummy' field
    )
