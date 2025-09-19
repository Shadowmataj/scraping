"""
amazon_data_scraper.py
This module contains the Amazon data scraper class for scraping product data based on ASIN.
It initializes the Selenium WebDriver, scrapes product details such as title, price, images,
and saving percentage, and handles potential pop-ups and login forms.
"""
from random import randint
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC

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


class AmazonDataScraper:
    """Main amazon data scraper class"""

    def __init__(self):
        """Initialize the scraper with a Selenium WebDriver instance."""
        self.driver = self.create_driver()

    @staticmethod
    def create_driver() -> webdriver.Remote:
        """Function to create and return a Selenium WebDriver instance."""
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-extensions")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option(name="detach", value=True)
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',  # URL of the remote server
            options=chrome_options
        )
        driver.delete_all_cookies()
        return driver

    def data_scraper(self, products: list, data: list) -> None:
        """Function to scrape data for a list of products."""
        for product in products:
            self.scrap_products_data(
                asin=product, data=data)

    def twister_scraper(self, asin: str) -> None:
        """Function to scrape twister data for a product identified by its ASIN."""
        try:
            # Extract the twister container
            twister_plus = self.driver.find_element(
                By.ID, "twister-plus-inline-twister")

            twister_options = twister_plus.find_elements(By.TAG_NAME, "ul")

            twister_list = []
            for option in twister_options:

                options_dict = {}
                option_attribute = option.get_attribute("data-a-button-group")
                option_name = option_attribute.split('"')[-2]

                options_dict["type"] = option_name

                options_list = option.find_elements(By.TAG_NAME, "li")
                for option_li in options_list:
                    option_asin = option_li.get_attribute("data-asin")
                    if option_asin == asin:
                        continue
                    options_dict["asin"] = option_asin

                    if option_name == 'color_name':
                        color_name = option_li.find_element(
                            By.TAG_NAME, "img").get_attribute("alt")
                        options_dict["name"] = color_name.lower().strip()
                    else:
                        option_swatch = option_li.find_element(
                            By.CLASS_NAME, 'swatch-title-text-container').text.lower().strip()
                        options_dict["name"] = option_swatch

                    twister_list.append({**options_dict})

            log = f'[{asin}] {COLORS["green"]}Twister.{COLORS["reset"]}\n'
            if len(twister_list):
                return (twister_list, log)
            else:
                raise NoSuchElementException(f'No Twister for {asin}.')
        except NoSuchElementException:
            return f'[{asin}] {COLORS["red"]}No Twister.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]}[ERROR] Twisters: {e} {COLORS["reset"]}")

    def scrap_products_data(self, asin: str, data: list) -> None:
        """Function to scrape data for a single product identified by its ASIN."""
        forbidden_images = ['HomeCustomProduct', 'play-icon-overla']
        logs = ''

        # Define allowed breadcrumbs to identify celphones
        allowed_breadcrums = [
            'banda ancha móvil',
            'celulares y smartphones de prepago',
            'celulares y smartphones desbloqueados'
        ]

        titles_filter = ['funda', 'case', 'protector', 'cristal',
                        'glass', 'mica', 'cable', 'audífono',
                        'headphone', 'earphone', 'bolígrafo',
                        'cover', 'ipad', 'tablet', 'watch', 'band',
                        'laptop', 'notebook', 'macbook', 'plan', 'cabezal',
                        'hotspot', 'router', 'fit3', 'SmartTag', 'sobremesa', 'HUAWEI 4G',
                        'computadora de bolsillo', 'galaxy book'
                        ]

        # Define the link to the product page
        link = f"https://www.amazon.com.mx/dp/{asin}"

        # Initialize the product dictionary with default values
        product = {
            "asin": asin,
            "price": 0,
            "url": link,
            "images": []
        }
        self.driver.get(link)

        # Handle potential pop-ups and login forms
        try:
            # Wait for the continue button to appear and click it
            continue_button = WebDriverWait(self.driver, randint(1, 4)).until(EC.visibility_of_element_located((
                By.CLASS_NAME, "a-button-text")))
            sleep(randint(2, 4))  # Sleep to avoid overwhelming the server
            continue_button.click()
            sleep(4)
            logs += f'[{asin}] {COLORS["green"]}Continue button.{COLORS["reset"]}\n'
        except:
            logs += f'[{asin}] {COLORS["red"]}No continue button.{COLORS["reset"]}\n'

        try:
            # Wait for the login form to appear
            WebDriverWait(self.driver, randint(1, 4)).until(EC.visibility_of_element_located((
                By.CLASS_NAME, "auth-workflow")))
            sleep(randint(2, 4))  # Sleep to avoid overwhelming the server
            logs += f'[{asin}] {COLORS["green"]}Login form.{COLORS["reset"]}\n'
            self.driver.get(link)
            sleep(4)
        except TimeoutException:
            logs += f'[{asin}] {COLORS["red"]}No login form.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]}[ERROR] Auth: {e}{COLORS["reset"]}")

        # Check if the product belongs to the celphone category
        try:
            # Wait for the breadcrumbs to appear
            # and check if they contain the allowed breadcrumbs
            breadcrumbs = WebDriverWait(self.driver, 8).until(EC.visibility_of_element_located((
                By.ID, "wayfinding-breadcrumbs_feature_div")))

            if any(breadcrumb in breadcrumbs.text.lower() for breadcrumb in allowed_breadcrums):
                logs += f'[{asin}] {COLORS["green"]}Celphone.{COLORS["reset"]}\n'
            else:
                raise Exception('The item is not a celphone.')
        except TimeoutException:
            logs += f'[{asin}] {COLORS["green"]}No breadcrumbs.{COLORS["reset"]}\n'
        except Exception:
            logs += f'[{asin}] {COLORS["red"]}Not a celphone.{COLORS["reset"]}\n'
            print(logs)
            del logs
            return

        # Scrape product details
        # Product title
        try:
            product_title = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.ID, "productTitle")))
            if product_title.text == '':
                raise NoSuchElementException('No title found.')
            lower_title = product_title.text.lower()
            if any(forbidden_title in lower_title for forbidden_title in titles_filter):
                if 'bundle' not in lower_title: raise Exception('The item is not a celphone.')
            product["title"] = product_title.text  # Store the product title
            logs += f'[{asin}] {COLORS["green"]}Product title.{COLORS["reset"]}\n'

        except TimeoutException:
            logs += f'[{asin}] {COLORS["red"]}No load.{COLORS["reset"]}\n'
            return
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}Not a celphone.{COLORS["reset"]}\n'
            return
        except Exception as e:
            logs += f'[{asin}] {COLORS["red"]}Not a celphone.{COLORS["reset"]}\n'
            print(logs)
            del logs
            return

        # Product images
        try:
            images_container = self.driver.find_element(
                By.CLASS_NAME, 'regularAltImageViewLayout')

            # Image URLs
            images = images_container.find_elements(By.TAG_NAME, "img")
            for image in images:
                image_link = image.get_attribute("src")
                if any(forbidden_image in image_link for forbidden_image in forbidden_images):
                    continue  # Skip non-product images
                image_split = image_link.split('_')
                image_split[-2] = f"{image_split[-2][:2]}679"
                image_link = '_'.join(image_split)
                product["images"].append({"url": image_link})

            logs += f'[{asin}] {COLORS["green"]}Images.{COLORS["reset"]}\n'
        except NoSuchElementException:
            images_container = self.driver.find_element(
                By.ID, 'altImages')

            # Image URLs
            images = images_container.find_elements(By.TAG_NAME, "img")
            for image in images:
                image_link = image.get_attribute("src")
                if any(forbidden_image in image_link for forbidden_image in forbidden_images):
                    continue  # Skip non-product images
                image_split = image_link.split('_')
                image_split[-2] = f"{image_split[-2][:2]}679"
                image_link = '_'.join(image_split)

                product["images"].append({"url": image_link})

            logs += f'[{asin}] {COLORS["red"]}No images.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]} [ERROR] Images: {e} {COLORS["reset"]}")

        # Product price
        try:
            price_container = self.driver.find_element(
                By.ID, 'corePriceDisplay_desktop_feature_div')
            product_price = price_container.find_element(
                By.CLASS_NAME, "a-price-whole")
            product_price_fraction = price_container.find_element(
                By.CLASS_NAME, "a-price-fraction")

            # Combine whole and fractional parts to form the complete price
            product["price"] = float(
                f"{product_price.text.replace(',', '')}.{product_price_fraction.text.replace('.', '')}")

            logs += f'[{asin}] {COLORS["green"]}Price.{COLORS["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}No price.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]} [ERROR] Price: {e} {COLORS["reset"]}")

        # Basis price and saving percentage
        try:
            saving_percentage = self.driver.find_element(
                By.CLASS_NAME, "savingsPercentage")

            # Extract and store the saving percentage if available
            if saving_percentage.text != '':
                saving_percentage = saving_percentage.text.replace(
                    "%", '').replace('-', '')
                product["saving_percentage"] = int(f"{saving_percentage}")

            logs += f'[{asin}] {COLORS["green"]}Saving.{COLORS["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}No saving.{COLORS["reset"]}\n'
        except Exception as e:
            print(
                f"{COLORS["red"]} [ERROR] Savind percentage: {e} {COLORS["reset"]}")

        try:
            basis_price = self.driver.find_element(
                By.ID, "corePriceDisplay_desktop_feature_div")
            basis_price_text = basis_price.find_element(
                By.CLASS_NAME, "basisPrice").text
            # Store the basis price if available
            basis_price_filtered = basis_price_text.split('\n')
            product["basis_price"] = float(
                basis_price_filtered[-1].replace('$', '').replace(',', ''))

            logs += f'[{asin}] {COLORS["green"]}Basis price.{COLORS["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}No basis price.{COLORS["reset"]}\n'
        except Exception as e:
            print(
                f"{COLORS["red"]} [ERROR] Basis price: {e} {COLORS["reset"]}")

        # Product twister ASIN
        twister = self.twister_scraper(asin=asin)
        if isinstance(twister, tuple):
            twister_list, log = twister
            product["twister"] = twister_list
            logs += log
        else:
            logs += twister
        # Product overview
        try:
            # Extract the product overview feature container
            feature_container = self.driver.find_element(
                By.ID, "productOverview_feature_div")
            # Extract features from the PoExpander

            try:
                feature_container.find_element(By.TAG_NAME, "a")
                feature_container.click()  # Click to expand the features
            except NoSuchElementException:
                pass
            except Exception as e:
                print(
                    f"{COLORS["red"]} [ERROR] PoExpander: {e} {COLORS["reset"]}")

            # Extract the table containing product features
            features_table = feature_container.find_elements(By.TAG_NAME, "tr")

            # Find the espefied product features
            specified_features = {
                "marca": "brand",
                "nombre del modelo": "model",
                "color": "color"
            }
            # Iterate through the features and extract the specified ones
            for feature_element in features_table:
                feature_list = feature_element.find_elements(By.TAG_NAME, "td")
                feature_name = feature_list[0].text.lower().strip()
                feature = feature_list[1].text.lower().strip()
                # Check if the feature name matches any of the specified features
                for specified_feature in specified_features.keys():
                    if specified_feature == feature_name:
                        product[specified_features[specified_feature]] = feature

            logs += f'[{asin}] {COLORS["green"]}Product overview.{COLORS["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}No product overview.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]} [ERROR] features: {e} {COLORS["reset"]}")

        # Product ranking
        try:
            # Extract the product details section
            aditional_info = self.driver.find_element(
                By.ID, "productDetails_db_sections")
            aditional_info_table = aditional_info.find_elements(
                By.TAG_NAME, "tr")
            # Initialize the ranking variable
            specified_aditional_info = 'clasificación en los más vendidos de amazon'
            custumers_opinion = 'opinión media de los clientes'

            # Iterate through the additional info table to find the specified ranking
            for info in aditional_info_table:
                header = info.find_element(By.TAG_NAME, "th").text.lower()
                # Check if the header matches the specified additional info
                if header == specified_aditional_info:
                    specified_ranking = 'celulares y smartphones desbloqueados'
                    rankings = info.find_elements(By.TAG_NAME, "li")
                    # Iterate through the rankings to find the specified ranking
                    for ranking in rankings:
                        ranking_text = ranking.text.lower()
                        # Check if the specified ranking is in the ranking text
                        if specified_ranking in ranking_text:
                            product["ranking"] = int(ranking_text.split(
                                ' ')[0].replace('nº', '').replace(',', ''))
                            break
                elif header == custumers_opinion:
                    custumers_opinion = info.find_element(
                        By.TAG_NAME, "td").text.lower().split('\n')[-1]
                    product["custumers_opinion"] = custumers_opinion

            if not product.get('ranking'):
                raise NoSuchElementException('Ranking not found.')

            logs += f'[{asin}] {COLORS["green"]}Ranking.{COLORS["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {COLORS["red"]}No ranking.{COLORS["reset"]}\n'
        except Exception as e:
            print(f"{COLORS["red"]} [ERROR] ranking: {e} {COLORS["reset"]}")

        # Print the logs for debugging
        print(logs)
        del logs

        data.append(product)  # Append the product data to the list

    def quit_driver(self):
        try:
            self.driver.quit()
        except InvalidSessionIdException:
            print(
                f"{COLORS['red']}Driver session already closed.{COLORS['reset']}")
        except Exception as e:
            print(
                f"{COLORS['red']}Error quitting driver: {e}{COLORS['reset']}")
