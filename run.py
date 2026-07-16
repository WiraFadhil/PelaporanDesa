import os
from config import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from app import app
from db import admins_col
from seed import seed_database

if __name__ == "__main__":
    if admins_col.count_documents({}) == 0:
        seed_database()
    print("Server running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
