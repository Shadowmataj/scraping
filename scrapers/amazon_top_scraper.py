"""
amazon_asin_scraper.py
This module contains the Amazon ASIN scraper class for scraping product data based on brand.
It initializes the Selenium WebDriver, performs a search for the brand, filters the results,
and scrapes the ASINs from the search results.
"""

from config import config

from time import sleep
from .base_amazon_scraper import BaseAmazonScraper
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AmazonTopScraper(BaseAmazonScraper):
    """Main Amazon ASIN scraper class for scraping product data based on brand."""

    def __init__(self):
        """Initialize the scraper with a Selenium WebDriver instance."""
        super().__init__()
        self.driver = self._create_driver(
            "--start-fullscreen",
            "--incognito",
        )
        self.amazon_top_url = config["amazon_top_url"]

    def main_method(self):
        """Main method to start the scraping process for top 100."""
        url = f"{self.amazon_url}/{self.amazon_top_url}"
        self.driver.get(url)

        self._asin_captchats(url=self.amazon_url)

        try:
            throttle = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, 'pre')))
            print("Throttle in the request has been raise.")
            self._quit_driver()
            return []
        except TimeoutError:
            print("No throttle.")
        except Exception:
            pass

        top_elements_dict = dict()
        while True:

            last_height = self.driver.execute_script(
                "return document.body.scrollHeight")

            while True:
                self.driver.execute_script(
                    f"window.scrollTo({last_height}, document.body.scrollHeight);")
                sleep(2)

                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            try:
                top_elements = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_all_elements_located((By.ID, 'gridItemRoot')))

                for top_element in top_elements:
                    ranking_raw = int(top_element.find_element(
                        By.CLASS_NAME, "zg-bdg-text").text.lower().replace("#", ""))
                    top_element_span = top_element.find_elements(
                        By.TAG_NAME, "span")
                    top_element_div = top_element_span[1].find_element(
                        By.TAG_NAME, "div")
                    top_element_asin = top_element_div.get_attribute("id")
                    top_elements_dict[top_element_asin] = ranking_raw

                next_page_button = self.driver.find_element(
                    By.CLASS_NAME, "a-last")
                next_page_button_class = next_page_button.get_attribute("class")
                if 'a-disabled' in next_page_button_class:
                    print("Cerrando driver...")
                    self._quit_driver()
                    return top_elements_dict
                next_page_button.click()
            except (Exception, TimeoutException):
                print("There has been an error during top 100 search (continue).")
                self._quit_driver()
                return[]
