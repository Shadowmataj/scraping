"""
amazon_data_scraper.py
This module contains the Amazon data scraper class for scraping product data based on ASIN.
It initializes the Selenium WebDriver, scrapes product details such as title, price, images,
and saving percentage, and handles potential pop-ups and login forms.
"""
from random import randint
from time import sleep

from .base_amazon_scraper import BaseAmazonScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


class AmazonDataScraper(BaseAmazonScraper):
    """Main amazon data scraper class"""

    def __init__(self):
        """Initialize the scraper with a Selenium WebDriver instance."""
        super().__init__()
        self.driver = self._create_driver(
            "--disable-notifications",
            "--incognito",
            "--disable-extensions",
            prefs={
                "profile.managed_default_content_settings.images": 2,
            },
            detach=True
        )

    def main_method(self, products: list) -> list:
        """Function to scrape data for a list of products."""
        data = list()
        for product in products:
            self._scrap_products_data(
                asin=product, data=data)
        self._quit_driver()
        return data

    def _twister_scraper(self, asin: str) -> None:
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

            log = f'[{asin}] {self.colors["green"]}Twister.{self.colors["reset"]}\n'
            if len(twister_list):
                return (twister_list, log)
            else:
                raise NoSuchElementException(f'No Twister for {asin}.')
        except NoSuchElementException:
            return f'[{asin}] {self.colors["red"]}No Twister.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]}[ERROR] Twisters: {e} {self.colors["reset"]}")

    def _scrap_products_data(self, asin: str, data: list) -> None:
        """Function to scrape data for a single product identified by its ASIN."""
        forbidden_images = ['HomeCustomProduct', 'play-icon-overla']
        logs = ''

        # Define allowed breadcrumbs to identify celphones
        allowed_breadcrums = [
            'banda ancha móvil',
            'celulares y smartphones de prepago',
            'celulares y smartphones desbloqueados'
        ]

        # Define the link to the product page
        link = f"{self.amazon_url}/dp/{asin}"

        # Initialize the product dictionary with default values
        product = {
            "asin": asin,
            "price": 0,
            "url": link,
            "brand": "",
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
            logs += f'[{asin}] {self.colors["green"]}Continue button.{self.colors["reset"]}\n'
        except:
            logs += f'[{asin}] {self.colors["red"]}No continue button.{self.colors["reset"]}\n'

        try:
            # Wait for the login form to appear
            WebDriverWait(self.driver, randint(1, 4)).until(EC.visibility_of_element_located((
                By.CLASS_NAME, "auth-workflow")))
            sleep(randint(2, 4))  # Sleep to avoid overwhelming the server
            logs += f'[{asin}] {self.colors["green"]}Login form.{self.colors["reset"]}\n'
            self.driver.get(link)
            sleep(4)
        except TimeoutException:
            logs += f'[{asin}] {self.colors["red"]}No login form.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]}[ERROR] Auth: {e}{self.colors["reset"]}")

        # Check if the product belongs to the celphone category
        try:
            # Wait for the breadcrumbs to appear
            # and check if they contain the allowed breadcrumbs
            breadcrumbs = WebDriverWait(self.driver, 8).until(EC.visibility_of_element_located((
                By.ID, "wayfinding-breadcrumbs_feature_div")))

            if any(breadcrumb in breadcrumbs.text.lower() for breadcrumb in allowed_breadcrums):
                logs += f'[{asin}] {self.colors["green"]}Celphone.{self.colors["reset"]}\n'
            else:
                raise Exception('The item is not a celphone.')
        except TimeoutException:
            logs += f'[{asin}] {self.colors["green"]}No breadcrumbs.{self.colors["reset"]}\n'
        except Exception:
            logs += f'[{asin}] {self.colors["red"]}Not a celphone.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
            return

        # Scrape product details
        # Product title
        try:
            product_title = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.ID, "productTitle")))
            if product_title.text == '':
                raise NoSuchElementException('No title found.')
            product["title"] = product_title.text  # Store the product title
            logs += f'[{asin}] {self.colors["green"]}Product title.{self.colors["reset"]}\n'

        except TimeoutException:
            logs += f'[{asin}] {self.colors["red"]}No load.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
            return
        except NoSuchElementException:
            logs += f'[{asin}] {self.colors["red"]}Not a celphone.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
            return
        except Exception as e:
            logs += f'[{asin}] {self.colors["red"]}Not a celphone.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
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

            logs += f'[{asin}] {self.colors["green"]}Images.{self.colors["reset"]}\n'
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

            logs += f'[{asin}] {self.colors["red"]}No images.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]} [ERROR] Images: {e} {self.colors["reset"]}")

        # Product price
        try:
            price_container = self.driver.find_element(
                By.ID, 'corePriceDisplay_desktop_feature_div')
            product_price = price_container.find_element(
                By.CLASS_NAME, "a-price-whole")
            product_price_fraction = price_container.find_element(
                By.CLASS_NAME, "a-price-fraction")

            # Combine whole and fractional parts to form the complete price
            final_price = float(
                f"{product_price.text.replace(',', '')}.{product_price_fraction.text.replace('.', '')}")

            if final_price < 601:
                raise Exception("Price is under $601")

            product["price"] = final_price

            logs += f'[{asin}] {self.colors["green"]}Price.{self.colors["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {self.colors["red"]}No price.{self.colors["reset"]}\n'
        except Exception as e:
            logs += f'[{asin}] {self.colors["red"]}Price under point price.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
            return

        # Basis price and saving percentage
        try:
            saving_percentage = self.driver.find_element(
                By.CLASS_NAME, "savingsPercentage")

            # Extract and store the saving percentage if available
            if saving_percentage.text != '':
                saving_percentage = saving_percentage.text.replace(
                    "%", '').replace('-', '')
                product["saving_percentage"] = int(f"{saving_percentage}")

            logs += f'[{asin}] {self.colors["green"]}Saving.{self.colors["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {self.colors["red"]}No saving.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]} [ERROR] Savind percentage: {e} {self.colors["reset"]}")

        try:
            basis_price = self.driver.find_element(
                By.ID, "corePriceDisplay_desktop_feature_div")
            basis_price_text = basis_price.find_element(
                By.CLASS_NAME, "basisPrice").text
            # Store the basis price if available
            basis_price_filtered = basis_price_text.split('\n')
            product["basis_price"] = float(
                basis_price_filtered[-1].replace('$', '').replace(',', ''))

            logs += f'[{asin}] {self.colors["green"]}Basis price.{self.colors["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {self.colors["red"]}No basis price.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]} [ERROR] Basis price: {e} {self.colors["reset"]}")

        # Product twister ASIN
        twister = self._twister_scraper(asin=asin)
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
                    f"{self.colors["red"]} [ERROR] PoExpander: {e} {self.colors["reset"]}")

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
                        if specified_feature == "marca":
                            if not any(default_brand in feature for default_brand in self.default_brands):
                                raise Exception("Not a specified brand.")
                            feature = feature.split(" ")[0]
                        product[specified_features[specified_feature]] = feature

            product_title_lower = product_title.text.lower()
            if product["brand"] == "":
                if "iphone" in product_title_lower:
                    product["brand"] = "apple"
                elif "poco" in product_title_lower:
                    product["brand"] = "xiaomi"
                else:
                    for default_brand in self.default_brands:
                        if default_brand in product_title_lower:
                            product["brand"] = default_brand
                            break

            if product["brand"] == "":
                print("Aún sin marca")
                raise Exception("Not a specified brand.")

            logs += f'[{asin}] {self.colors["green"]}Product overview.{self.colors["reset"]}\n'

        except NoSuchElementException:
            product_title_lower = product_title.text.lower()
            if product["brand"] == "":
                if "iphone" in product_title_lower:
                    product["brand"] = "apple"
                elif "poco" in product_title_lower:
                    product["brand"] = "xiaomi"
                else:
                    for default_brand in self.default_brands:
                        if default_brand in product_title_lower:
                            product["brand"] = default_brand
                            break
            if product["brand"] == "":
                print("Aún sin marca")
                raise Exception("Not a specified brand.")

            logs += f'[{asin}] {self.colors["red"]}No product overview.{self.colors["reset"]}\n'
        except Exception as e:
            logs += f'[{asin}] {self.colors["red"]}Not a specified brand.{self.colors["reset"]}\n'
            print(logs)
            del logs
            del product
            return

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

            logs += f'[{asin}] {self.colors["green"]}Ranking.{self.colors["reset"]}\n'
        except NoSuchElementException:
            logs += f'[{asin}] {self.colors["red"]}No ranking.{self.colors["reset"]}\n'
        except Exception as e:
            print(
                f"{self.colors["red"]} [ERROR] ranking: {e} {self.colors["reset"]}")

        # Print the logs for debugging
        print(logs)
        del logs

        data.append(product)  # Append the product data to the list
