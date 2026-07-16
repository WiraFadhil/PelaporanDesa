from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

admins_col = db["admins"]
reports_col = db["reports"]
categories_col = db["categories"]
residents_col = db["residents"]
settings_col = db["settings"]
announcements_col = db["announcements"]
