"""Configuration Module
This module loads environment variables from a .env file and provides configuration settings
for the application, including IP address, Selenium server URL, Amazon URLs, and color codes.
"""

import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "ip": os.getenv("IP"),
    "selenium_url": os.getenv("SELENIUM_URL"),
    "amazon_url": os.getenv("A_URL"),
    "amazon_top_url": os.getenv("A_TOP_URL"),
    "colors": {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": '\033[0m'
    },
    "brands": [],
    "credentials": os.getenv("CREDENTIALS_PATH")
}
