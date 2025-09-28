"""Main function for the scraper process."""
import sys
import os
import json
import traceback

from time import sleep
from getpass import getpass
from config import config
from pathlib import Path

from custom_exceptions import (
    TokenExpiredError,
    InvalidCredentials)
from scrapers import (
    AmazonScraperManager,
    AmazonAsinScraper,
    AmazonDataScraper,
    AmazonTopScraper
)


def save_tokens(scraper: AmazonScraperManager, file: Path):
    with file.open('w') as f:
        tokens = {
            "access_token": scraper.token or "",
            "refresh_token": scraper.refresh_token or ""
        }
        json.dump(tokens, f, indent=4)

    print(
        f"\n{config["colors"]["green"]}Tokens have been saved.{config["colors"]["reset"]}")


def menu(scraper: AmazonScraperManager, file: Path):
    if not file.exists():
        with file.open('w') as f:
            json.dump({}, f, indent=4)

    while True:

        with file.open('r') as f:
            read_tokens = json.load(f)
            scraper.set_credentials(
                read_tokens.get("access_token") or "",
                read_tokens.get("refresh_token") or ""
            )

        while not scraper.token:
            print("To begin the program is necesary to login:")
            email = input("Email: ")
            password = getpass("Password: ")
            try:
                scraper.login(email, password)
            except InvalidCredentials as e:
                print(
                    f"{config["colors"]["red"]}{str(e)}{config["colors"]["reset"]}")
            sleep(3)
            os.system("clear")

        print("Starting program...\n\n")
        print("Select an option: ")
        print("1.- Regular update.")
        print("2.- Add a new brands.")
        print("3.- Exit.")
        option = int(input("Select an option: "))

        match option:
            case 1:
                print("Starting regular update procces, this may take a while...")
                try:
                    scraper.restore_brands()
                    scraper.main()
                except TokenExpiredError as e:
                    print(
                        f"{config["colors"]["red"]}{str(e)}{config["colors"]["red"]}")
                finally:
                    print("Finishing regular update.")
            case 2:
                new_brands = input("Enter the new brand (, separated): ")
                nbs_ls = new_brands.split(",")
                print("Starting new brands search...")
                try:
                    scraper.update_brands(nbs_ls)
                    scraper.main()
                except TokenExpiredError as e:
                    print(
                        f"{config["colors"]["red"]}{str(e)}{config["colors"]["reset"]}")
                finally:
                    print("Finishing new brands search.")
            case 3:
                save_tokens(scraper=scraper, file=file)
                sys.exit(0)
            case _:
                print("Invalid option.")

        print("Finishing program...")


def main():
    amazon_scrapper_manager = AmazonScraperManager(
        AmazonAsinScraper,
        AmazonDataScraper,
        AmazonTopScraper
    )

    file = Path(config["credentials"])
    try:
        menu(scraper=amazon_scrapper_manager, file=file)
    except KeyboardInterrupt as e:
        save_tokens(scraper=amazon_scrapper_manager, file=file)
        raise KeyboardInterrupt(e)


# Run the main function if this script is executed directly
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            f"\n{config["colors"]["red"]}\n\n[KeyboardInterrupt] Closing main program...{config["colors"]["reset"]}")
    except Exception as e:
        print(f"{config["colors"]["red"]}Error:")
        traceback.print_exc()
        print(f"{config["colors"]["reset"]}")
    sleep(2)
