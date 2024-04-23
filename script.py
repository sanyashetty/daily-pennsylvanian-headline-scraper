"""
Scrapes a headline from The Daily Pennsylvanian website and saves it to a 
JSON file that tracks headlines over time.
"""

import os
import sys

import daily_event_monitor

import bs4
import requests
import loguru

SECTIONS = {
    "Opinion": "https://www.thedp.com/section/opinion",
    "Multimedia": "https://www.thedp.com/multimedia",
    "Podcasts": "https://www.thedp.com/section/podcasts"
}

TO_SCRAPE = os.getenv("SECTIONS", "Opinion,Multimedia,Podcasts").split(",")

def scrape_data_point(section):
    """
    Scrapes the main headline from The Daily Pennsylvanian home page.

    Returns:
        str: The headline text if found, otherwise an empty string.
    """
    url = SECTIONS[section]
    req = requests.get(url)
    loguru.logger.info(f"Request URL: {req.url}")
    loguru.logger.info(f"Request status code: {req.status_code}")

    if req.ok:
        soup = bs4.BeautifulSoup(req.text, "html.parser")

        if section in ["Podcasts", "Opinion"]:
            target_element = soup.find("h3", class_="standard-link")  # Adjust class as needed
        elif section == "Multimedia":
            target_element = soup.find("a", class_="medium-link")  # Adjust as needed
        
        data_point = "" if target_element is None else target_element.text
        loguru.logger.info(f"Data point: {data_point}")
        return data_point


if __name__ == "__main__":

    # Setup logger to track runtime
    loguru.logger.add("scrape.log", rotation="1 day")

    # Create data dir if needed
    loguru.logger.info("Creating data directory if it does not exist")
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    # Load daily event monitor
    loguru.logger.info("Loading daily event monitor")
    dem = daily_event_monitor.DailyEventMonitor(
        "data/daily_pennsylvanian_headlines.json"
    )

    # Run scrape
    loguru.logger.info("Starting scrape")
    results = {}
    for section in TO_SCRAPE:
        loguru.logger.info(f"Scraping section: {section}")
        try:
            headline = scrape_data_point(section)
        except Exception as e:
            loguru.logger.error(f"Failed to scrape section {section}: {e}")
            headline = None
        if headline:
            results[section] = headline

    serialized_results = json.dumps(results)

    # Save data
    if serialized_results is not None:
        dem.add_today(serialized_results)
        dem.save()
        loguru.logger.info("Saved daily event monitor")

    def print_tree(directory, ignore_dirs=[".git", "__pycache__"]):
        loguru.logger.info(f"Printing tree of files/dirs at {directory}")
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(directory, "").count(os.sep)
            indent = " " * 4 * (level)
            loguru.logger.info(f"{indent}+--{os.path.basename(root)}/")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                loguru.logger.info(f"{sub_indent}+--{file}")

    print_tree(os.getcwd())

    loguru.logger.info("Printing contents of data file {}".format(dem.file_path))
    with open(dem.file_path, "r") as f:
        loguru.logger.info(f.read())

    # Finish
    loguru.logger.info("Scrape complete")
    loguru.logger.info("Exiting")
