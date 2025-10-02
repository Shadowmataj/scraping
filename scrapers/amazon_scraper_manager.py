"""
Amazon Scraper Manager
This module manages the scraping process for Amazon products using multiple threads.
It initializes the scrapers, processes the product data, and saves the results to a JSON fileƒ
"""

import os
import requests
import threading

from getpass import getpass
from time import sleep
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Type, TypeVar

from config import config
from custom_exceptions import InvalidCredentials
from .base_amazon_scraper import BaseAmazonScraper

T = TypeVar("T", bound="BaseAmazonScraper")


class AmazonScraperManager():
    """Manager class"""

    def __init__(self, data_scraper: Type[T], asin_scraper: Type[T], top_scraper: Type[T]):
        """Initialize the AmazonScraperManager with configuration settings."""
        self.colors: dict = config["colors"]
        self.ip: str = config["ip"]
        self.threads: int = os.cpu_count()
        self.token: str = str()
        self.refresh_token: str = str()
        self.header: dict = dict()
        self.brands: list = config["brands"]
        self.asins_to_update_list: list = list()
        self.products: list = list()
        self.amazon_asin_scraper: Type[T] = data_scraper
        self.amazon_data_scraper: Type[T] = asin_scraper
        self.top_scraper: Type[T] = top_scraper

    def _api_request(
        self, func: Callable[..., requests.Response],
            endpoint: str,
            **options: dict) -> dict:
        """Make a request to the API. Handle token expiration and re-authentication."""
        while True:
            options["url"] = f"{self.ip}{endpoint}"
            response = func(**options)

            response_json = response.json()
            if not response_json.get("error"):
                return response_json
            
            messages = [
                "Signature verification failed.",
                "The token has expired",
                "Token not provided"
            ]
            if response_json["message"] in messages:
                {'error': 'invalid_token', 'message': 'Signature verification failed.'}
                if self.refresh_token:
                    self.token = self.refresh_token
                    self.refresh_token = str()
                    self.header["Authorization"] = f"Bearer {self.token}"
                else:
                    self.token = str()
                    while not self.token:
                        print("Login required:")
                        email = input("Email: ")
                        password = getpass("Password: ")
                        try:
                            self.login(email, password)

                        except InvalidCredentials as e:
                            print(
                                f"{config["colors"]["red"]}{str(e)}{config["colors"]["reset"]}")
                        sleep(3)
                options["headers"] = self.header

    def login(self, email: str, password: str) -> str:
        """Log in to the API and retrieve an access token."""
        credentials = {
            "email": email,
            "password": password
        }
        login_response = self._api_request(
            func=requests.post,
            endpoint="/api/login",
            json=credentials
        )

        if not login_response.get("access_token"):
            if login_response["status"] == "Unauthorized":
                raise InvalidCredentials(f"{login_response["status"]}")
        else:
            self.token = login_response["access_token"]
            self.refresh_token = login_response["refresh_token"]
            self.header["Authorization"] = f"Bearer {self.token}"
            print(f"{self.colors["green"]}Login success{self.colors["reset"]}")

    def _get_brands(self) -> list:
        """Get the list of brands."""
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
            print(
                f"{self.colors["red"]}Using default brands.{self.colors["reset"]}")
            return brands

        api_brands = brands_response["brands"]

        if not len(api_brands):
            return brands

        for filter in brands_filter:
            try:
                api_brands.remove(filter)
            except ValueError:
                pass
        for api_brand in api_brands:
            api_brand = api_brand.split(" ")[0]

        return api_brands

    def restore_brands(self):
        self.brands = config["brands"] = self._get_brands()
        print("The brands have been restored.")

    def update_brands(self, new_brands: list) -> None:
        self.brands = config["brands"] = new_brands
        print(
            f"{self.colors["purple"]}Brands have been updated.{self.colors["reset"]}")
        sleep(2)

    def set_credentials(self, token: str, refresh_token: str):
        self.token = token
        self.refresh_token = refresh_token
        self.header["Authorization"] = f"Bearer {self.token}"

    def _get_asins(self) -> list:
        """Get the list of ASINs."""
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
        try:
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
                            f"{self.colors['red']}Error en scraper: {e}{self.colors["reset"]}")
        except KeyboardInterrupt:
            print(
                f"{self.colors['red']}Process interrupted by user.{self.colors['reset']}")
            executor.shutdown(wait=False, cancel_futures=True)
            print(f"{self.colors['red']}Shutting down scrapers...{self.colors['reset']}")
            
            print(
                f"{self.colors['red']}All scrapers have been closed.{self.colors['reset']}")
            raise KeyboardInterrupt

        except Exception as e:
            print(
                f"{self.colors['red']}ThreadPoolExecutor error: {e}{self.colors['reset']}")

        # Return the scraped data

    def _start_scrapers(self) -> list:
        """Main function to start the scraping process."""

        print(f"Searching for this brands:")
        for brand_to_search in self.brands:
            print(
                f"{self.colors['blue']}{brand_to_search}{self.colors['reset']}")

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

        print(
            f"Products found: {self.colors['blue']}{first_acc}{self.colors['reset']}.")

        # Append the ASINs to the data list
        final_dict = {}
        for brand, asins in asins_by_brand.items():
            print(
                f"Processing {self.colors['blue']}{brand.title()}: {len(asins)}{self.colors['reset']} products...")
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
                f"{brand.title()} products processed: {self.colors['blue']}{len(products)}/{len(asins)}{self.colors['reset']}.")

        del asins_by_brand  # Clear the ASINs dictionary to free memory

        last_acc = 0
        for brand, asins in final_dict.items():
            last_acc += len(asins)
        # Print the final results
        print(
            f"Products scraped: {self.colors["blue"]}{last_acc}/{first_acc}{self.colors["reset"]}.")

        return final_dict

    def main(self) -> None:
        """Main entry point for the scraper manager. It handles the login, scraping process, and saving the results."""

        products_dict = self._start_scrapers()

        for key, value in products_dict.items():

            put_response = self._api_request(
                func=requests.put,
                endpoint="/api/products/amazon",
                json=value,
                headers=self.header
            )

            print(f"{self.colors['cyan']}{put_response}{self.colors['reset']}")

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
                print(
                    f"{self.colors["cyan"]}{post_response}{self.colors["reset"]}")
