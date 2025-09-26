import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "email": os.getenv("EMAIL"),
    "password": os.getenv("PASSWORD"),
    "ip": os.getenv("IP"),
    "selenium_url": os.getenv("SELENIUM_URL"),
    "amazon_url": os.getenv("A_URL"),
    "amazon_top_url": os.getenv("A_TOP_URL") 
}