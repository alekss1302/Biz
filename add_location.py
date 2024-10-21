from pymongo import MongoClient
import random

# Define bounding boxes for different towns
locations = {
    "Coleraine": [55.10653864221481, -6.703013870894064, 55.16083114339611, -6.640640630380869],
    "Banbridge": [54.32805966474902, -6.29894073802459, 54.36914017698541, -6.238287009221747],
    # Add other towns as needed
}

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

# Loop through each town and assign random coordinates within the bounding box
for location in locations:
    for business in businesses.find({"town": location}):
        rand_x = locations[location][0] + ((locations[location][2] - locations[location][0]) * (random.randint(0, 100) / 100))
        rand_y = locations[location][1] + ((locations[location][3] - locations[location][1]) * (random.randint(0, 100) / 100))
        businesses.update_one(
            {"_id": business["_id"]},  # Match the business
            {"$set": {
                "location": {"type": "Point", "coordinates": [rand_x, rand_y]}  # Set GeoJSON location
            }}
        )


from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

# Select a random business
for business in businesses.aggregate([{"$sample": {"size": 1}}]):
    print("Random business is " + business["name"] + " from " + business["town"])

    # Find the nearest 10 neighbors to the selected business
    for neighbour in businesses.aggregate([
        {"$geoNear": {
            "near": {"type": "Point", "coordinates": business["location"]["coordinates"]},
            "maxDistance": 50000,  # Max distance of 50km
            "minDistance": 1,  # Exclude the business itself
            "distanceField": "distance",  # Field name for distance in output
            "spherical": True  # Use spherical geometry for Earth-like distance
        }},
        {"$project": {"name": 1, "town": 1, "distance": 1}},  # Project name, town, and distance
        {"$limit": 10}  # Limit results to 10
    ]):
        distance_km = str(round(neighbour["distance"] / 1000))  # Convert distance to kilometers
        print(neighbour["name"] + " from " + neighbour["town"] + " is " + distance_km + "km away")
