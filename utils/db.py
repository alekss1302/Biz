# utils/db.py
from pymongo import MongoClient
from config import config

client = MongoClient(config.DATABASE_URI)
db = client['bizDB']
