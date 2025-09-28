"""
amazon_asin_scraper.py
This module contains the Amazon ASIN scraper class for scraping product data based on brand.
It initializes the Selenium WebDriver, performs a search for the brand, filters the results,
and scrapes the ASINs from the search results.
"""

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
from selenium.webdriver.common.keys import Keys


class AmazonAsinScraper(BaseAmazonScraper):
    """Main Amazon ASIN scraper class for scraping product data based on brand."""

    def __init__(self):
        """Initialize the scraper with a Selenium WebDriver instance."""
        super().__init__()
        self.driver = self._create_driver(
            "--start-fullscreen",
            "--incognito"
        )
        self.current_link = ""

    def main_method(self, brand_list: list) -> dict:
        """Main method to start the scraping process for a given brand."""
        asins_dict = dict()

        categories = [
            'banda ancha móvil',
            'celulares y smartphones de prepago',
            'celulares y smartphones desbloqueados'
        ]

        for brand in brand_list:
            # Initialize the data list for the brand
            data = []
            self.driver.get(self.amazon_url)
            self._brand_search(brand)
            self._brand_filtering(brand)
            self._category_filtering(brand=brand)
            main_page = self.driver.current_url
            for category in categories:
                if self._category_filtering(brand=brand, category=category):
                    self._asins_scrape(brand, data)
                    self.driver.get(main_page)
            asins_dict[brand] = data
            self._quit_driver()
        return asins_dict

    def _brand_search(self, brand: str):
        """Method to search for the brand on Amazon."""

        logs = f"{self.colors['green']}Searching for brand: {brand}.{self.colors['reset']}\n"
        # Handle any captcha or authentication issues
        self._asin_captchats(url=self.amazon_url)

        # Find the search input field and enter the brand name
        # This is to search for the brand on Amazon
        try:
            # Wait for the search input field to be visible and enter the brand name
            nav_var_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'twotabsearchtextbox')))

            # Enter the brand name into the search input field
            nav_var_input.send_keys(brand)
            nav_var_input.send_keys(Keys.ENTER)
            logs += f"{self.colors['green']}Brand '{brand}' searched successfully.{self.colors['reset']}\n"
        except TimeoutException:
            # If the search input field is not found, try to find it in the navigation bar
            # This is a fallback in case the search input field is not available
            logs += f"{self.colors['red']}Search input field not found (trying navigation bar).{self.colors['reset']}\n"
            nav_var_input = WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((By.ID, 'nav-bb-search')))
            nav_var_input.send_keys(brand)
            nav_var_input.send_keys(Keys.ENTER)
            logs += f"{self.colors['green']}Brand '{brand}' searched successfully in navigation bar.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error searching for brand.{self.colors['reset']}\n"

        print(logs)  # Print logs for debugging
        del logs  # Clear logs after printing

    def _brand_filtering(self, brand: str):
        """Method to filter the search results by brand."""

        self._asin_captchats(url=self.amazon_url)

        logs = f"{self.colors['green']}Filtering by brand: {brand}.{self.colors['reset']}\n"
        brand_list = brand.split(" ")
        try:
            for _ in range(len(brand_list)):
                # Find the brands refinements section and click on the brand checkboxes
                # This is to filter the search results by the specified brand
                brands_refinements = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "brandsRefinements")))
                # Find all the brand list items in the refinements section
                a_list_item = brands_refinements.find_elements(
                    By.CLASS_NAME, "a-list-item")
                # Iterate through the brand list items and click on the checkboxes
                # This is to select the checkboxes for the specified brand
                while len(a_list_item):
                    element = a_list_item.pop()
                    lower_element = element.text.lower()
                    if lower_element in brand_list:
                        checkbox = element.find_element(By.TAG_NAME, "i")
                        brand_list.remove(lower_element)
                        checkbox.click()
                        break
            logs += f"{self.colors['green']}Brand '{brand}' filtered successfully.{self.colors['reset']}\n"
        except TimeoutException:
            logs += f"{self.colors['red']}[ERROR] Brand filtering failed.{self.colors['reset']}\n"
        except NoSuchElementException:
            logs += f"{self.colors['red']}No brand refinements found.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error filtering brands.{self.colors['reset']}\n"

        print(logs)  # Print logs for debugging
        del logs  # Clear logs after printing

    def _category_filtering(self, brand:str, category: str = 'celulares y accesorios') -> bool:
        """Method to filter the search results by category."""

        self._asin_captchats(url=self.amazon_url)

        logs = f"{self.colors['green']}Filtering {brand} by category: {category}.{self.colors['reset']}\n"
        try:
            # Wait for the departments section to be visible and select the 'Celulares y accesorios' department
            # This is to ensure that the search results are filtered to the correct category
            departments = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "departments")))

            # Find all the department options and click on the 'Celulares y accesorios' option
            department_options = departments.find_elements(By.TAG_NAME, "a")

            for department in department_options:
                if department.text.lower() == category:
                    department.click()
                    logs += f"{self.colors['green']}Category '{category}' filtered successfully.{self.colors['reset']}\n"
                    print(logs)
                    del logs
                    return True
        except TimeoutException:
            logs += f"{self.colors['red']}[ERROR] {category} filtering failed.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error filtering {category}.{self.colors['reset']}\n"

        print(logs)
        del logs  # Clear logs after printing

        return False

    def _asins_scrape(self, brand: str, data: list):
        """Method to scrape ASINs from the search results."""

        logs = f"{self.colors['green']}Scraping {brand} ASINs.{self.colors['reset']}\n"
        asin_list = []
        count = 1
        color_count = 0
        analysed_count = 0
        titles_filter = [
            'funda', 'case', 'protector', 'cristal',
            'glass', 'mica', 'cable', 'audífono', 'galaxy tab'
            'headphone', 'earphone', 'bolígrafo',
            'cover', 'ipad', 'tablet', 'watch', 'band',
            'laptop', 'notebook', 'macbook', 'plan', 'cabezal',
            'hotspot', 'router', 'fit3', 'SmartTag', 'sobremesa', 'HUAWEI 4G',
            'computadora de bolsillo', 'galaxy book', 'carcasa', 'smarttag',
            '(E5783-230a)', 'udio DRC-15PF', 'ME993LLA', 'Guía Completa DA61-00524A'
        ]
        # Handle any captcha or authentication issues
        self._asin_captchats(url=self.amazon_url)
        # Wait for the search results to load and find if the category is not empty
        try:
            WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="search"]/div[1]/div[1]/div/span[1]/div[1]/div[2]/div/div/div/h3/span')))
            logs += f"{self.colors['red']}Empty results loaded successfully (exit).{self.colors['reset']}\n"
            return
        except TimeoutException:
            logs += f"{self.colors['green']}Search results not loaded (continue).{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['green']}[ERROR] Error loading search results (continue).{self.colors['reset']}\n"

        # If the last element is not found, try to find the search results header
        # This is to handle cases where the search results page structure might differ
        try:
            WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="search"]/div[1]/div[1]/div/span[1]/div[1]/div[1]/div/div/div/h3/span')))
            logs += f"{self.colors['red']}Empty results header found (exit).{self.colors['reset']}\n"
            return
        except TimeoutException:
            logs += f"{self.colors['green']}Search results header not found (continue).{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['green']}[ERROR] Finding Empty results header (continue).{self.colors['reset']}\n"

        while True:
            try:
                # Search for the products count element to ensure the page has loaded
                products_count = WebDriverWait(self.driver, 1).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "s-breadcrumb-header-text")))
                logs += f"{self.colors['green']}Products count found: {products_count.text}.{self.colors['reset']}\n"
            except TimeoutException:
                logs += f"{self.colors['red']}[ERROR] No products found.{self.colors['reset']}\n"
            except Exception:
                logs += f"{self.colors['red']}[ERROR] Error finding products count.{self.colors['reset']}\n"

            items = []
            sleep(4)
            items = self.driver.find_elements(By.CLASS_NAME, "s-asin")

            # Iterate through the product items and collect their ASINs
            for item in items:

                title_tag = item.find_element(By.TAG_NAME, "h2")
                title = title_tag.text.lower()

                if any(word in title for word in titles_filter):
                    continue

                analysed_count += 1

                # Get the ASIN from the data-asin attribute
                data_asin = item.get_attribute("data-asin")

                # If the ASIN is valid, add it to the list
                if data_asin != '':
                    # Check for color variations of the product
                    colors = item.find_elements(
                        By.CLASS_NAME, "s-color-swatch-pad")

                    # If color variations exist, add their ASINs as well
                    if len(colors):
                        color_count += 1
                        for color in colors:
                            color_link = color.find_element(
                                By.TAG_NAME, "div").get_attribute("data-csa-c-swatch-url")
                            color_asin = color_link.split("/")[3]
                            count += 1
                            asin_list.append(color_asin)
                        continue
                    count += 1
                    asin_list.append(data_asin)

            try:
                # Check if there is a next page button and click it to go to the next page
                next_page_button = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((
                    By.CLASS_NAME, "s-pagination-next")))
                if "s-pagination-disabled" in next_page_button.get_attribute("class"):
                    break
                self.current_link = next_page_button.get_attribute("href")
                next_page_button.click()
            except TimeoutException:
                logs += f"{self.colors['red']}[ERROR] No next page button found(exit).{self.colors['reset']}\n"
                break
            except ElementClickInterceptedException:
                logs += f"{self.colors['red']}[ERROR] Next page button not clickable (refresh).{self.colors['reset']}\n"
                self.driver.refresh()
            except Exception:
                logs += f"{self.colors['red']}[ERROR] Error clicking next page (exit).{self.colors['reset']}\n"
                break

        print(logs)
        del logs  # Clear logs after printing

        # Remove duplicate ASINs and prepare the final response
        data.extend(list(set(asin_list)))
        sleep(4)  # Sleep to avoid overwhelming the server
