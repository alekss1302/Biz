from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

# Select a random business
for business in businesses.aggregate([{"$sample": {"size": 1}}]):
    print("Random business is " + business["name"] + " from " + business["town"])

    # Find the 10 nearest neighbors to the selected business
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
