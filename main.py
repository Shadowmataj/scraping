"""Main function for the scraper process."""

from scrapers import (
    AmazonScraperManager,
    AmazonAsinScraper,
    AmazonDataScraper,
    AmazonTopScraper
)

# Run the main function if this script is executed directly
if __name__ == "__main__":

    amazon_scrapper_manager = AmazonScraperManager(
        AmazonAsinScraper,
        AmazonDataScraper,
        AmazonTopScraper
    )

    print('Starting process...')
    amazon_scrapper_manager.main()
    print('Finishing program...')
