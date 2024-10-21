from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz  # Select the 'biz' collection

# Define the aggregation pipeline to match businesses from Banbridge and project specific fields
pipeline = [
    {"$match": {"town": "Banbridge"}},  # Select businesses from Banbridge
    {"$project": {"town": 1, "profit": 1}}  # Only return 'town' and 'profit' fields
]

# Execute the aggregation pipeline
for business in businesses.aggregate(pipeline):
    # Output town and the profit for the year 2024 (index 2 in the 'profit' array)
    print(business["town"], str(business["profit"][2]["gross"]))

pipeline = [
    {"$match": {"town": "Banbridge"}},  # Match businesses from Banbridge
    {"$project": {"town": 1, "profit": 1, "num_employees": 1}},  # Project specific fields
    {"$unwind": "$profit"},  # Unwind the 'profit' array
    {"$match": {"num_employees": {"$gte": 50}, "profit.gross": {"$gte": 0}}},  # Match conditions for employees and profit
    {"$sort": {"profit.gross": -1}}  # Sort by gross profit in descending order
]

# Execute the aggregation pipeline
for business in businesses.aggregate(pipeline):
    print(business)


pipeline = [
    {"$match": {"town": "Banbridge"}},
    {"$project": {"town": 1, "profit": 1, "num_employees": 1}},
    {"$unwind": "$profit"},
    {"$match": {"num_employees": {"$gte": 50}, "profit.gross": {"$gte": 0}}},
    {"$sort": {"profit.gross": -1}},
    {"$skip": 2},  # Skip the first 2 results
    {"$limit": 3}  # Limit the output to 3 results
]

# Execute the pipeline
for business in businesses.aggregate(pipeline):
    print(business)


pipeline = [
    {"$match": {"town": "Banbridge"}},
    {"$project": {"town": 1, "profit": 1, "num_employees": 1, "_id": 0}},  # Exclude _id field
    {"$unwind": "$profit"},
    {"$match": {"num_employees": {"$gte": 50}, "profit.gross": {"$gte": 0}}},
    {"$out": "profitable_big_biz"}  # Output to new collection 'profitable_big_biz'
]

# Execute the pipeline
businesses.aggregate(pipeline)


pipeline = [
    {"$match": {"town": "Banbridge"}},
    {"$project": {"town": 1, "profit": 1, "num_employees": 1, "_id": 0}},
    {"$unwind": "$profit"},
    {"$match": {"num_employees": {"$gte": 50}, "profit.gross": {"$gte": 0}}},
    {"$group": {
        "_id": None,  # Group all results together
        "count": {"$sum": 1},  # Count the number of documents
        "total": {"$sum": "$profit.gross"},  # Sum the gross profits
        "average": {"$avg": "$profit.gross"},  # Calculate the average gross profit
        "max": {"$max": "$profit.gross"},  # Find the max gross profit
        "min": {"$min": "$profit.gross"}  # Find the min gross profit
    }}
]

# Execute the aggregation pipeline
for summary in businesses.aggregate(pipeline):
    print(summary)
