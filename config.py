import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "email": os.getenv("EMAIL"),
    "password": os.getenv("PASSWORD"),
    "ip": os.getenv("IP")
}