from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

# First, get the number of businesses in each town using the $group stage
pipeline = [
    {
        "$group": {
            "_id": "$town",  # Group by town
            "count": {"$sum": 1}  # Count the number of businesses
        }
    }
]

# Execute the aggregation pipeline
print("Number of businesses in each town:")
for result in businesses.aggregate(pipeline):
    print(f"{result['_id']}: {result['count']} businesses")

# Next, find the most profitable business in each town for each year
years = ["2022", "2023", "2024"]  # Available years for profit data

for year in years:
    print(f"\nMost profitable business for {year}:")

    # Define the pipeline to find the most profitable business in each town for the given year
    pipeline = [
        {"$unwind": "$profit"},  # Unwind the profit array
        {"$match": {"profit.year": year}},  # Filter by the specific year
        {
            "$group": {
                "_id": "$town",  # Group by town
                "max_profit": {"$max": "$profit.gross"},  # Find the maximum gross profit
                "business_name": {"$first": "$name"},  # Take the business name
                "town": {"$first": "$town"}  # Include town name
            }
        },
        {"$sort": {"_id": 1}}  # Sort by town name
    ]

    # Execute the aggregation pipeline
    for result in businesses.aggregate(pipeline):
        print(f"{result['town']}: {result['business_name']} with a profit of {result['max_profit']}")
