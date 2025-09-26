"""Base Amazon Scraper"""

from selenium import webdriver
from config import config

from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseAmazonScraper():
    """Base amazon scraper class"""

    def __init__(self):
        self.colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": '\033[0m'
        }
        self.default_brands = BRANDS = [
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
        self.selenium_url = config["selenium_url"]
        self.amazon_url = config["amazon_url"]
        self.current_url = ""

    def _create_driver(self, *arguments: str, **kwargs: dict | bool) -> webdriver.Remote:
        """Function to create and return a Selenium WebDriver instance."""
        chrome_options = webdriver.ChromeOptions()

        if arguments:
            for argument in arguments:
                chrome_options.add_argument(argument)

        if kwargs:
            for key, value in kwargs.items():
                chrome_options.add_experimental_option(name=key, value=value)

        driver = webdriver.Remote(
            command_executor=self.selenium_url,  # URL of the remote server
            options=chrome_options
        )
        return driver

    def _asin_captchats(self, url: str):
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
            self.driver.get(self.current_url)
            logs += f"{self.colors['green']}Authentication workflow completed successfully.{self.colors['reset']}\n"
        except TimeoutException:
            logs += f"{self.colors['green']}Authentication workflow not found.{self.colors['reset']}\n"
        except Exception:
            logs += f"{self.colors['red']}[ERROR] Error waiting for authentication workflow.{self.colors['reset']}\n"

        print(logs)  # Print logs for debugging
        del logs  # Clear logs after printing

    def _quit_driver(self):
        try:
            self.driver.quit()
        except InvalidSessionIdException:
            print(
                f"{self.colors['red']}Driver session already closed.{self.colors['reset']}")
        except Exception as e:
            print(
                f"{self.colors['red']}Error quitting driver: {e}{self.colors['reset']}")
