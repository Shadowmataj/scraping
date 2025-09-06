"""
Amazon Scraper Manager
This module manages the scraping process for Amazon products using multiple threads.
It initializes the scrapers, processes the product data, and saves the results to a JSON fileƒ
"""

import os
import json
import requests

from time import sleep
from concurrent.futures import ThreadPoolExecutor

from scrapers.amazon_asin_scraper import AmazonAsinScraper
from scrapers.amazon_data_scraper import AmazonDataScraper

DATA = './scraped_data/data.json'
THREADS = os.cpu_count()
BRANDS = [
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


def data_process(products: list):
    """Function to process the products using multiple threads.
    It initializes the AmazonDataScraper for each thread and scrapes the product data."""
    data_scrapers = []

    # Check if the products list is empty
    items = len(products) // THREADS
    difference_count = len(products) % THREADS
    if items == 0:
        workers = len(products)
    else:
        workers = THREADS

    # Create scrapers
    for _ in range(workers):
        amazon_scraper = AmazonDataScraper()
        data_scrapers.append(amazon_scraper)

    executor_list = []
    data = []
    # Use ThreadPoolExecutor to manage threads
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        step = 0
        for scraper in data_scrapers:
            start = step
            step = start + items
            if difference_count > 0:
                step += 1
                difference_count -= 1

            products_list = products[start:step]
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

def asin_process(brands: list) -> dict:
    """Function to process the ASINs using multiple threads.
    It initializes the AmazonAsinScraper for each thread and scrapes the ASINs"""

    asin_scrapers = []

    # Check if the products list is empty
    items = len(brands) // THREADS
    difference_count = len(brands) % THREADS
    if items == 0:
        workers = len(brands)
    else:
        workers = THREADS

    # Create scrapers
    for _ in range(workers):
        amazon_asin_scraper = AmazonAsinScraper()
        asin_scrapers.append(amazon_asin_scraper)

    executor_list = []
    asins_dict = {}
    # Use ThreadPoolExecutor to manage threads
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        step = 0
        for scraper in asin_scrapers:
            start = step
            step = start + items
            if difference_count > 0:
                step += 1
                difference_count -= 1

            brands_list = brands[start:step]
            executor_list.append(
                executor.submit(scraper.main_method,
                                brands_list, asins_dict)
            )
    # Wait for all threads to complete
    for _ in executor_list:
        pass

    # Return the scraped data
    return asins_dict

def main(brands_to_search: list = ['oppo']) -> list:
    """Main function to start the scraping process."""
    # Main execution starts here
    print(
        f"Searching for this brands:")
    for brand_to_search in brands_to_search:
        print(f"{COLORS['blue']}{brand_to_search}{COLORS['reset']}")

    # Start the ASIN scraper
    asins_by_brand = asin_process(brands=brands_to_search) # Scrape ASINs

    sleep(8)  # Sleep to avoid overwhelming the server

    # Prints the number of products found
    first_acc = 0
    for brand, asins in asins_by_brand.items():
        first_acc += len(asins)

    print(f"Products found: {COLORS['blue']}{first_acc}{COLORS['reset']}.")

    # Append the ASINs to the data list
    final_dict = {}
    for brand, asins in asins_by_brand.items():
        print(f"Processing {COLORS['blue']}{brand.title()}: {len(asins)}{COLORS['reset']} products...")
        products = data_process(asins)  # Process the ASINs
        sleep(8)  # Sleep to avoid overwhelming the server
        final_dict[brand] = products
        sleep(8)  # Sleep to avoid overwhelming the server
        print(f"{brand.title()} products processed: {COLORS['blue']}{len(products)}/{len(asins)}{COLORS['reset']}.")    

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

    products_dict = main(brands_to_search=BRANDS)

    sleep(8)

    for key, value in products_dict.items():
        response = requests.put('http://localhost:80/api/products/amazon', json=value)
        print(response.text)
    # with open(DATA, 'w') as file:
    #     json.dump(products_dict, file)


    print('Finishing program...')
