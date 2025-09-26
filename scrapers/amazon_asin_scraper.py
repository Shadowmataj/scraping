"""
amazon_asin_scraper.py
This module contains the Amazon ASIN scraper class for scraping product data based on brand.
It initializes the Selenium WebDriver, performs a search for the brand, filters the results,
and scrapes the ASINs from the search results.
"""

from time import sleep
from .base_amazon_scraper import BaseAmazonScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    InvalidSessionIdException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class AmazonAsinScraper(BaseAmazonScraper):
    """Main Amazon ASIN scraper class for scraping product data based on brand."""

    def __init__(self):
        """Initialize the scraper with a Selenium WebDriver instance."""
        super().__init__()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-fullscreen")
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',  # URL of the remote server
            options=chrome_options
        )
        self.driver.delete_all_cookies()

    def main_method(self, brand_list: list, asins_dict: dict):
        """Main method to start the scraping process for a given brand."""
        categories = [
            'banda ancha móvil',
            'celulares y smartphones de prepago',
            'celulares y smartphones desbloqueados'
        ]
        for brand in brand_list:
            # Initialize the data list for the brand
            data = []
            self.driver.get('https://amazon.com.mx')
            self.brand_search(brand)
            self.brand_filtering(brand)
            self.category_filtering(category='celulares y accesorios')
            main_page = self.driver.current_url
            for category in categories:
                if self.category_filtering(category=category):
                    self.asins_scrape(brand, data)
                    self.driver.get(main_page)
            asins_dict[brand] = data
            sleep(2)
            self.quit_driver()

    def captchats(self):
        """Method to handle captcha or authentication issues."""
        logs = f"{self.colors['green']}Handling captcha or authentication issues.{self.colors['reset']}\n"
        # Wait for the continue button and click it if it appears
        # This is to handle any pop-ups or modals that might appear
        # when accessing the Amazon homepage
        try:
            continue_button = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((
                By.CLASS_NAME, "a-button-text")))
            continue_button.click()
            logs += f"{self.colors['green']}Continue button clicked successfully.{self.colors['reset']}\n"
            logs = f"{self.colors['red']}Captcha detected.{self.colors['reset']}\n"
        except TimeoutException:
            logs += f"{self.colors['green']}Continue button not found.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error clicking continue button.{self.colors['reset']}\n"

        # Wait for the authentication workflow to complete
        # This is to ensure that the page is fully loaded before performing any actions
        try:
            WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((
                By.CLASS_NAME, "auth-workflow")))
            self.driver.get('https://amazon.com.mx')
            logs += f"{self.colors['green']}Authentication workflow completed successfully.{self.colors['reset']}\n"
        except TimeoutException:
            logs += f"{self.colors['green']}Authentication workflow not found.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error waiting for authentication workflow.{self.colors['reset']}\n"

        print(logs)  # Print logs for debugging
        del logs  # Clear logs after printing

    def brand_search(self, brand: str):
        """Method to search for the brand on Amazon."""
        logs = f"{self.colors['green']}Searching for brand: {brand}.{self.colors['reset']}\n"

        self.captchats()  # Handle any captcha or authentication issues

        # Find the search input field and enter the brand name
        # This is to search for the brand on Amazon
        try:
            # Wait for the search input field to be visible and enter the brand name
            nav_var_input = WebDriverWait(self.driver, 1).until(
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

    def brand_filtering(self, brand: str):
        """Method to filter the search results by brand."""
        logs = f"{self.colors['green']}Filtering by brand: {brand}.{self.colors['reset']}\n"
        brand_list = brand.split(" ")

        self.captchats()  # Handle any captcha or authentication issues
        try:
            for _ in range(len(brand_list)):
                # Find the brands refinements section and click on the brand checkboxes
                # This is to filter the search results by the specified brand
                brands_refinements = WebDriverWait(self.driver, 1).until(
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

    def category_filtering(self, category: str = 'Celulares y accesorios') -> bool:
        """Method to filter the search results by category."""
        logs = f"{self.colors['green']}Filtering by category: {category}.{self.colors['reset']}\n"
        self.captchats()  # Handle any captcha or authentication issues
        try:
            # Wait for the departments section to be visible and select the 'Celulares y accesorios' department
            # This is to ensure that the search results are filtered to the correct category
            departments = WebDriverWait(self.driver, 1).until(
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

    def asins_scrape(self, brand: str, data: list):
        """Method to scrape ASINs from the search results."""
        logs = f"{self.colors['green']}Scraping {brand} ASINs.{self.colors['reset']}\n"
        asin_list = []
        count = 1
        color_count = 0
        analysed_count = 0
        self.captchats()  # Handle any captcha or authentication issues
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
                analysed_count += 1

                # Get the ASIN from the data-asin attribute
                data_asin = item.get_attribute("data-asin")

                # If the ASIN is valid, add it to the list
                if data_asin != '':
                    # Check for color variations of the product
                    self.colors = item.find_elements(
                        By.CLASS_NAME, "s-color-swatch-pad")

                    # If color variations exist, add their ASINs as well
                    if len(self.colors):
                        color_count += 1
                        for color in self.colors:
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

    def quit_driver(self):
        try:
            self.driver.quit()
        except InvalidSessionIdException:
            print(
                f"{self.colors['red']}Driver session already closed.{self.colors['reset']}")
        except Exception as e:
            print(
                f"{self.colors['red']}Error quitting driver: {e}{self.colors['reset']}")
