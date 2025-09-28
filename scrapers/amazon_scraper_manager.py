"""
Amazon Scraper Manager
This module manages the scraping process for Amazon products using multiple threads.
It initializes the scrapers, processes the product data, and saves the results to a JSON fileƒ
"""

import os
import requests
import threading

from time import sleep
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Type, TypeVar

from config import config
from .base_amazon_scraper import BaseAmazonScraper

T = TypeVar("T", bound="BaseAmazonScraper")

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


class AmazonScraperManager():
    """Manager class"""

    def __init__(self, data_scraper: Type[T], asin_scraper: Type[T], top_scraper: Type[T]):
        """"""
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.credentials = {
            "email": config["email"],
            "password": config["password"]
        }
        self.ip = config["ip"]
        self.threads = os.cpu_count()
        self.token = self._login()
        self.header = {
            "Authorization": f"Bearer {self.token}"
        }
        self.brands = config["brands"] = self._get_brands()
        self.asins_to_update_list = self._get_asins()
        self.products = []
        self.amazon_asin_scraper = data_scraper
        self.amazon_data_scraper = asin_scraper
        self.top_scraper = top_scraper

    def _api_request(
        self, func: Callable[..., requests.Response],
            endpoint: str,
            **options: dict) -> dict:
        """"""
        options["url"] = f"{self.ip}{endpoint}"
        response = func(**options)
        return response.json()

    def _login(self) -> str:
        """"""
        login_response = self._api_request(
            func=requests.post,
            endpoint="/api/login",
            json=self.credentials
        )

        return login_response["access_token"]

    def _get_brands(self) -> list:
        """"""
        brands = [
            'samsung', 'apple', 'xiaomi', 'oppo',
            'huawei', 'motorola', 'sony', 'nokia',
            'cubot', 'google', 'nubia', 'zte'
        ]

        brands_filter = [
            None,
            '',
            "generic"
        ]

        brands_response = self._api_request(
            func=requests.get,
            endpoint="/api/brands/amazon",
            headers=self.header
        )

        if not brands_response.get("brands"):
            return brands

        api_brands = brands_response["brands"]

        if not len(api_brands):
            return brands

        for filter in brands_filter:
            try:
                api_brands.remove(filter)
            except ValueError:
                pass
        return api_brands

    def _get_asins(self) -> list:
        """"""
        asins_response = self._api_request(
            func=requests.get,
            endpoint="/api/products/amazon/id",
            headers=self.header
        )

        if asins_response.get("asins"):
            return asins_response["asins"]

        return []

    def _scraper_process(
            self, list_to_split: list,
            scraper_class: Type[T],
            data: list | dict) -> list | dict:
        """Function to process the ASINs using multiple threads.
        It initializes the AmazonAsinScraper for each thread and scrapes the ASINs"""

        scrapers_list = list()

        # Check if the products list is empty
        items = len(list_to_split) // self.threads
        difference_count = len(list_to_split) % self.threads
        if items == 0:
            workers = len(list_to_split)
        else:
            workers = self.threads

        # Create scrapers
        for lap in range(workers):
            scraper_instance = scraper_class()
            scrapers_list.append(scraper_instance)

        # Use ThreadPoolExecutor to manage threads
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor_list = []
            step = 0
            for scraper in scrapers_list:
                start = step
                step = start + items
                if difference_count > 0:
                    step += 1
                    difference_count -= 1

                splited_list = list_to_split[start:step]
                executor_list.append(
                    executor.submit(scraper.main_method,
                                    splited_list)
                )
            # Wait for all threads to complete
            lock = threading.Lock()
            for future in as_completed(executor_list):
                try:
                    result = future.result()
                    if result:
                        with lock:
                            if isinstance(data, dict):
                                for key, value in result.items():
                                    data[key] = value
                            elif isinstance(data, list):
                                data.extend(result)
                except Exception as e:
                    print(
                        f"{COLORS['red']}Error en scraper: {e}{COLORS["reset"]}")

        # Return the scraped data

    def _start_scrapers(self) -> list:
        """Main function to start the scraping process."""

        print("Starting top 100 products search.")
        top_scraper = self.top_scraper()
        top_100 = top_scraper.main_method()
        print(f"Top elements found: {len(top_100)}")

        print(f"Searching for this brands:")
        for brand_to_search in self.brands:
            print(f"{COLORS['blue']}{brand_to_search}{COLORS['reset']}")

        # Start the ASIN scraper
        asins_by_brand = dict()
        self._scraper_process(
            list_to_split=self.brands,
            scraper_class=self.amazon_asin_scraper,
            data=asins_by_brand
        )  # Scrape ASINs

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
            products = list()
            self._scraper_process(
                list_to_split=asins,
                scraper_class=self.amazon_data_scraper,
                data=products
            )  # Process the ASINs
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

    def main(self) -> None:
        """"""

        products_dict = self._start_scrapers()

        for key, value in products_dict.items():

            put_response = self._api_request(
                func=requests.put,
                endpoint="/api/products/amazon",
                json=value,
                headers=self.header
            )

            print(f"{COLORS['cyan']}{put_response}{COLORS['reset']}")

            pending_asins = put_response["to_create"]
            pending_list = []

            if len(pending_asins):
                for product in value:
                    if product["asin"] in pending_asins:
                        pending_list.append(product)

                post_response = self._api_request(
                    func=requests.post,
                    endpoint="/api/products/amazon",
                    json=pending_list,
                    headers=self.header
                )
                print(f"{COLORS["cyan"]}{post_response}{COLORS["reset"]}")
