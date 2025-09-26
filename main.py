"""Main function for the scraper process."""

from scrapers.amazon_scraper_manager import AmazonScraperManager
from scrapers.amazon_asin_scraper import AmazonAsinScraper
from scrapers.amazon_data_scraper import AmazonDataScraper

# Run the main function if this script is executed directly
if __name__ == "__main__":

    amazon_scrapper_manager = AmazonScraperManager(
        AmazonAsinScraper,
        AmazonDataScraper)

    print('Starting process...')
    amazon_scrapper_manager.main()
    print('Finishing program...')
