"""
Amazon Scraper Manager
This module manages the scraping process for Amazon products using multiple threads.
It initializes the scrapers, processes the product data, and saves the results to a JSON fileƒ
"""

import os
import requests

from time import sleep
from concurrent.futures import ThreadPoolExecutor

from scrapers.amazon_asin_scraper import AmazonAsinScraper
from scrapers.amazon_data_scraper import AmazonDataScraper

from dotenv import load_dotenv

DATA = './scraped_data/data.json'
THREADS = os.cpu_count()

COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "purple": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": '\033[0m'
}

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')


class AmazonScraperManager():
    """Manager class"""

    def __init__(self):
        """"""
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.ip = os.getenv("IP")
        self.threads = os.cpu_count()
        self.token = self.login()
        self.header = {
            "Authorization": f"Bearer {self.token}"
        }
        self.brands = self.get_brands()
        self.asins_to_update_list = self.get_asins()
        self.products = []

    def login(self):
        """"""
        login_response = requests.post(
            f"{self.ip}/api/login",
            json={
                "email": self.email,
                "password": self.password
            })

        login_json = login_response.json()
        return login_json["access_token"]

    def get_brands(self):
        """"""
        brands = [
            'samsung',
            'apple',
            'xiaomi',
            'oppo',
            'huawei',
            'motorola',
            'sony',
            'nokia',
            'cubot',
            'google',
            'nubia',
            'zte'
        ]

        brands_response = requests.get(
            f"{self.ip}/api/brands/amazon",
            headers=self.header
        )

        brands_json = brands_response.json()
        if brands_json.get("brands"):
            return brands_json["brands"]

        return brands

    def get_asins(self):
        """"""
        asins_response = requests.get(
            f"{self.ip}/api/products/amazon/id",
            headers=self.header
        )

        asins_json = asins_response.json()
        if asins_json.get("asins"):
            return asins_json["asins"]

        return []
    
    def asin_process(self) -> dict:
        """Function to process the ASINs using multiple threads.
        It initializes the AmazonAsinScraper for each thread and scrapes the ASINs"""

        asin_scrapers = []

        # Check if the products list is empty
        items = len(self.brands) // self.threads
        difference_count = len(self.brands) % self.threads
        if items == 0:
            workers = len(self.brands)
        else:
            workers = self.threads

        # Create scrapers
        for _ in range(workers):
            amazon_asin_scraper = AmazonAsinScraper()
            asin_scrapers.append(amazon_asin_scraper)

        executor_list = []
        asins_dict = {}
        # Use ThreadPoolExecutor to manage threads
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            step = 0
            for scraper in asin_scrapers:
                start = step
                step = start + items
                if difference_count > 0:
                    step += 1
                    difference_count -= 1

                brands_list = self.brands[start:step]
                executor_list.append(
                    executor.submit(scraper.main_method,
                                    brands_list, asins_dict)
                )
        # Wait for all threads to complete
        for _ in executor_list:
            pass

        # Return the scraped data
        return asins_dict



    def data_process(self):
        """Function to process the products using multiple threads.
        It initializes the AmazonDataScraper for each thread and scrapes the product data."""
        data_scrapers = []

        # Check if the products list is empty
        items = len(self.products) // self.threads
        difference_count = len(self.products) % self.threads
        if items == 0:
            workers = len(self.products)
        else:
            workers = self.threads

        # Create scrapers
        for _ in range(workers):
            amazon_scraper = AmazonDataScraper()
            data_scrapers.append(amazon_scraper)

        executor_list = []
        data = []
        # Use ThreadPoolExecutor to manage threads
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            step = 0
            for scraper in data_scrapers:
                start = step
                step = start + items
                if difference_count > 0:
                    step += 1
                    difference_count -= 1

                products_list = self.products[start:step]
                executor_list.append(
                    executor.submit(scraper.data_scraper,
                                    products_list, data)
                )
        # Wait for all threads to complete
        for _ in executor_list:
            pass

        # # Close all scrapers
        for scraper in data_scrapers:
            scraper.quit_driver()

        # Return the scraped data
        return data


    def main(self) -> list:
        """Main function to start the scraping process."""
        # Main execution starts here
        print(
            f"Searching for this brands:")
        for brand_to_search in self.brands:
            print(f"{COLORS['blue']}{brand_to_search}{COLORS['reset']}")

        # Start the ASIN scraper
        asins_by_brand = self.asin_process(brands=self.brands)  # Scrape ASINs

        sleep(8)  # Sleep to avoid overwhelming the server

        # Prints the number of products found
        first_acc = 0
        for brand, asins in asins_by_brand.items():
            first_acc += len(asins)

        print(f"Products found: {COLORS['blue']}{first_acc}{COLORS['reset']}.")

        # Append the ASINs to the data list
        final_dict = {}
        for brand, asins in asins_by_brand.items():
            print(
                f"Processing {COLORS['blue']}{brand.title()}: {len(asins)}{COLORS['reset']} products...")
            products = self.data_process(asins)  # Process the ASINs
            sleep(8)  # Sleep to avoid overwhelming the server
            final_dict[brand] = products
            sleep(8)  # Sleep to avoid overwhelming the server
            print(
                f"{brand.title()} products processed: {COLORS['blue']}{len(products)}/{len(asins)}{COLORS['reset']}.")

        del asins_by_brand  # Clear the ASINs dictionary to free memory

        last_acc = 0
        for brand, asins in final_dict.items():
            last_acc += len(asins)
        # Print the final results
        print(
            f"Products scraped: {COLORS["blue"]}{last_acc}/{first_acc}{COLORS["reset"]}.")

        return final_dict


# Run the main function if this script is executed directly
if __name__ == "__main__":
    print('Starting process...')

    amazon_scrapper_manager = AmazonScraperManager()

    products_dict = amazon_scrapper_manager.main()

    sleep(8)

    for key, value in products_dict.items():
        post_response = requests.put(
            'http://167.88.45.40:5000/api/products/amazon',
            json=value,
            headers={
                "Authorization": f"Bearer {access_token}"
            })
        print(post_response.text)
        post_json = post_response.json()
        pending_asins = post_json["to_create"]
        pending_list = []
        if len(pending_asins):
            for product in value:
                if product["asin"] in pending_asins:
                    pending_list.append(product)

            post_response = requests.post(
                'http://167.88.45.40:5000/api/products/amazon',
                json=pending_list,
                headers={
                    "Authorization": f"Bearer {access_token}"
                })

    print('Finishing program...')
