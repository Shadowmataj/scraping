"""
amazon_asin_scraper.py
This module contains the Amazon ASIN scraper class for scraping product data based on brand.
It initializes the Selenium WebDriver, performs a search for the brand, filters the results,
and scrapes the ASINs from the search results.
"""
import os
import threading

from concurrent.futures import ThreadPoolExecutor, as_completed
from config import config
from selenium import webdriver

from time import sleep
from random import randint
from .base_amazon_scraper import BaseAmazonScraper
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,

)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AmazonTopScraper(BaseAmazonScraper):
    """Main Amazon ASIN scraper class for scraping product data based on brand."""

    def __init__(self, ):
        """Initialize the scraper with a Selenium WebDriver instance."""
        super().__init__()
        self.driver = self._create_driver(
            "--start-fullscreen",
            "--incognito",
        )
        self.amazon_top_url = config["amazon_top_url"]
        self.threads = os.cpu_count() * 2

    def _scraper_process(
        self,
        list_to_split: list,
        data: list) -> list:
        """Function to manage the scraping process using multiple threads."""

        # Check if the products list is empty
        items = len(list_to_split) // self.threads
        difference_count = len(list_to_split) % self.threads
        if items == 0:
            workers = len(list_to_split)
        else:
            workers = self.threads

        # Use ThreadPoolExecutor to manage threads
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor_list = []
                step = 0
                for _ in range(workers):
                    start = step
                    step = start + items
                    if difference_count > 0:
                        step += 1
                        difference_count -= 1

                    splited_list = list_to_split[start:step]
                    executor_list.append(
                        executor.submit(self._scrap_top_100_data,
                                        self._create_driver(
                                            "--disable-notifications",
                                            "--incognito",
                                            "--disable-extensions",
                                            prefs={
                                                "profile.managed_default_content_settings.images": 2,
                                            },
                                            detach=True
                                        ),
                                        splited_list
                                        )
                    )
                # Wait for all threads to complete
                lock = threading.Lock()
                for future in as_completed(executor_list):
                    try:
                        result = future.result()
                        with lock:
                            data.extend(result)

                    except Exception as e:
                        print(
                            f"{self.colors['red']}Error en scraper: {e}{self.colors['reset']}")

        except KeyboardInterrupt:
            print(
                f"{self.colors['red']}Process interrupted by user.{self.colors['reset']}")
            executor.shutdown(wait=False, cancel_futures=True)
            print(
                f"{self.colors['red']}Shutting down scrapers...{self.colors['reset']}")

            print(
                f"{self.colors['red']}All scrapers have been closed.{self.colors['reset']}")
            raise KeyboardInterrupt

        except Exception as e:
            print(
                f"{self.colors['red']}ThreadPoolExecutor error: {e}{self.colors['reset']}")


    def main_method(self) -> dict:
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
                next_page_button_class = next_page_button.get_attribute(
                    "class")
                if 'a-disabled' not in next_page_button_class:
                    next_page_button.click()
                    continue
                self._quit_driver()
                break
            except Exception as e:
                print(
                    f"{self.colors['red']}There has been an error during top 100 search: {str(e)}.{self.colors['reset']}")
                self._quit_driver()
                return []

        try:
            extracted_twisters_list = list()
            self._scraper_process(
                list_to_split=[
                    {k: v} for k, v in top_elements_dict.items()
                ],
                data=extracted_twisters_list
            )
            for item in extracted_twisters_list:
                for asin, value in item.items():
                    if asin not in top_elements_dict:
                        top_elements_dict[asin] = value

            return top_elements_dict

        except Exception as e:
            print(
                f"{self.colors['red']}There has been an error during top 100 twister search: {e}.{self.colors['reset']}")
            self._quit_driver()
            return {}

    def _scrap_top_100_data(self, driver: webdriver.Remote, asins: list) -> list:
        """Scrape product data for a given ASIN and append it to the data list."""
        data = list()
        for item in asins:
            for asin, value in item.items():
                logs = ''
                temp_data = list()
                # Define the link to the product page
                link = f"{self.amazon_url}/dp/{asin}"

                driver.get(link)
                # Handle potential pop-ups and login forms
                try:
                    # Wait for the continue button to appear and click it
                    continue_button = WebDriverWait(driver, randint(1, 4)).until(EC.visibility_of_element_located((
                        By.CLASS_NAME, "a-button-text")))
                    # Sleep to avoid overwhelming the server
                    sleep(randint(2, 4))
                    continue_button.click()
                    sleep(4)
                    logs += f'[{asin}] {self.colors["green"]}Continue button.{self.colors["reset"]}\n'
                except:
                    logs += f'[{asin}] {self.colors["red"]}No continue button.{self.colors["reset"]}\n'

                try:
                    # Wait for the login form to appear
                    WebDriverWait(driver, randint(1, 4)).until(EC.visibility_of_element_located((
                        By.CLASS_NAME, "auth-workflow")))
                    # Sleep to avoid overwhelming the server
                    sleep(randint(2, 4))
                    logs += f'[{asin}] {self.colors["green"]}Login form.{self.colors["reset"]}\n'
                    driver.get(link)
                    sleep(4)
                except TimeoutException:
                    logs += f'[{asin}] {self.colors["red"]}No login form.{self.colors["reset"]}\n'
                except Exception as e:
                    print(
                        f"{self.colors["red"]}[ERROR] Auth: {e}{self.colors["reset"]}")
                try:
                    # Extract the twister container
                    twister_plus = driver.find_element(
                        By.ID, "twister-plus-inline-twister")

                    twister_options = twister_plus.find_elements(
                        By.TAG_NAME, "ul")

                    for option in twister_options:
                        # Extract the ASIN from the option
                        options_list = option.find_elements(By.TAG_NAME, "li")
                        for option_li in options_list:
                            option_asin = option_li.get_attribute("data-asin")
                            if option_asin == asin:
                                continue
                            temp_data.append({option_asin: value})

                    logs += f'[{asin}] {self.colors["green"]}Twister.{self.colors["reset"]}\n'
                    if not len(temp_data):
                        raise NoSuchElementException(
                            f'No top 100 twister for {asin}.')
                    print(logs)
                    del logs
                    data.extend(temp_data)

                except NoSuchElementException:
                    logs = f'[{asin}] {self.colors["red"]}No top 100 Twister.{self.colors["reset"]}\n'
                    print(logs)
                    del logs
                except Exception as e:
                    print(
                        f"{self.colors["red"]}[ERROR] Top 100 twisters: {e} {self.colors["reset"]}")

        driver.quit()
        return data

    