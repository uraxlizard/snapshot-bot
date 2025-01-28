import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import os
import mariadb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YouTubeSearchScreenshot:
    def __init__(self, db_config, output_dir="screenshots"):
        self.base_url = "https://www.youtube.com/results"
        self.output_dir = output_dir
        self.driver = None
        self.db_config = db_config
        self.records = []
        self.prefix = ""
        self.video_position = ""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def setup_driver(self):
        """Set up the Chrome WebDriver using undetected_chromedriver."""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            self.driver = uc.Chrome(options=options)
        except Exception as e:
            logging.error(f"Error setting up WebDriver: {e}")
            raise
            
    def fetch_prefix_from_db(self):
        """Fetching Prefix for searching query from DB"""
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            query = """
            SELECT 
                settings.search_prefix
            FROM 
                settings
            """
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                self.prefix = result[0]
            cursor.close()
            conn.close()
        except mariadb.Error as e:
            logging.error(f"Error connecting to MariaDB: {e}")

    def fetch_records_from_db(self):
        """Fetch records from the database where screen_shot = TRUE."""
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            query = """
            SELECT 
                campaigns.id,
                campaigns.geo_location,
                campaigns.search_query, 
                campaigns.keyword, 
                campaigns.video_name
            FROM 
                campaigns
            WHERE 
                campaigns.snapshot = FALSE
            """
            cursor.execute(query)
            self.records = cursor.fetchall()
            cursor.close()
            conn.close()
            logging.info(f"Fetched {len(self.records)} records from the database.")
        except mariadb.Error as e:
            logging.error(f"Error connecting to MariaDB: {e}")
            
    def update_record_status(self, record_id, screenshot_path, video_position):
        """Update the record status to processed (TRUE) and set snapshot_url in the database."""
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Update the campaigns table
            update_campaign_query = """
            UPDATE campaigns
            SET 
                snapshot = TRUE,
                ranking_position = %s,
                updated_at = %s
            WHERE 
                id = %s
            """
            cursor.execute(update_campaign_query, (video_position, current_time, record_id))

            # Insert into the snapshots table
            insert_snapshot_query = """
            INSERT INTO snapshots (campaign_id, snapshot_file, ranking_position, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_snapshot_query, (record_id, screenshot_path, video_position, current_time, current_time))

            conn.commit()
            cursor.close()
            conn.close()

            logging.info(f"Record with ID {record_id} updated in campaigns and inserted into snapshots with snapshot_url: {screenshot_path}.")
        except mariadb.Error as e:
            logging.error(f"Error updating record ID {record_id}: {e}")

    def navigate_to_search_results(self, search_query, geo_location):
        """Navigate to the YouTube search results page."""
        try:
            self.driver.get(f"{self.base_url}?search_query={search_query}&gl={geo_location}")
            self.accept_terms_and_conditions()
            time.sleep(2)
            self.driver.get(f"{self.base_url}?search_query={search_query}&gl={geo_location}")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
        except Exception as e:
            logging.error(f"Error navigating to search results for query '{search_query}': {e}")

    def accept_terms_and_conditions(self):
        """Accept YouTube's terms and conditions if prompted."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='yt-spec-button-shape-next yt-spec-button-shape-next--filled yt-spec-button-shape-next--mono yt-spec-button-shape-next--size-m' and (@aria-label='Accept the use of cookies and other data for the purposes described' or @aria-label='\u041f\u0440\u0438\u0435\u043c\u0430\u043d\u0435 \u043d\u0430 \u0438\u0437\u043f\u043e\u043b\u0437\u0432\u0430\u043d\u0435\u0442\u043e \u043d\u0430 \u201e\u0431\u0438\u0441\u043a\u0432\u0438\u0442\u043a\u0438\u201c \u0438 \u0434\u0440\u0443\u0433\u0438 \u0434\u0430\u043d\u043d\u0438 \u0437\u0430 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0442\u0435 \u0446\u0435\u043b\u0438')]")
            )).click()
            logging.info("Accepted terms and conditions.")
        except Exception:
            logging.info("No terms and conditions prompt found.")

    def search_and_screenshot(self, record_id, title):
        """Search for the term on the page and capture a screenshot of the first result, with a numbered overlay."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)
    
            for _ in range(4):
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
                
            time.sleep(2)
    
            elements = self.driver.find_elements(By.XPATH, f"//ytd-video-renderer[.//yt-formatted-string[contains(text(), '{title}')]]")
            if elements:
                for index, element in enumerate(elements, start=1):
                    self.driver.execute_script("arguments[0].style.border = '5px solid red';", element)
                    
                    self.driver.execute_script(f"""
                    let numLabel = document.createElement('div');
                    numLabel.style.position = 'absolute';
                    numLabel.style.background = 'red';
                    numLabel.style.color = 'white';
                    numLabel.style.padding = '10px';
                    numLabel.style.fontSize = '36px';
                    numLabel.style.fontWeight = 'bold';
                    numLabel.style.width = '50px';
                    numLabel.style.height = '50px';
                    numLabel.style.borderRadius = '50%';
                    numLabel.style.display = 'flex';
                    numLabel.style.alignItems = 'center';
                    numLabel.style.justifyContent = 'center';
                    numLabel.style.zIndex = '10000';
                    numLabel.textContent = '{index}';
                    let rect = arguments[0].getBoundingClientRect();
                    numLabel.style.left = (rect.left + window.scrollX - 25) + 'px';
                    numLabel.style.top = (rect.top + window.scrollY - 25) + 'px';
                    document.body.appendChild(numLabel);
                    """, element)
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(2)
    
                    if output_dir is None:
                        output_dir = self.default_output_dir

                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    screenshot_path = os.path.join(output_dir, f"{record_id}_{self.timestamp}_screenshot.png")
                    try:
                        self.driver.save_screenshot(screenshot_path)
                        logging.info(f"Screenshot saved at {screenshot_path}")
                    except Exception as e:
                        logging.warning(f"Element screenshot failed, falling back to full-page screenshot: {e}")
                        return None

                    self.video_position = index
    
                    return screenshot_path
            else:
                logging.warning(f"Search term '{title}' not found on the page.")
                return None
    
        except Exception as e:
            logging.error(f"Error during search and screenshot for term '{title}': {e}")
            return None

    def teardown(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed.")
            except Exception as e:
                logging.error(f"Error while quitting the WebDriver: {e}")
            finally:
                self.driver = None

    def process_records(self):
        """Process all records fetched from the database."""
        for record in self.records:
            record_id, geo_location, search_query, keyword, title = record
            self.navigate_to_search_results(self.prefix + " " + search_query, geo_location)
            screenshot_path = self.search_and_screenshot(record_id, title)
            if screenshot_path:
                self.update_record_status(record_id, screenshot_path, self.video_position)

if __name__ == "__main__":
    scraper = YouTubeSearchScreenshot(
        db_config={
            "host": "127.0.0.1",
            "user": "root",
            "password": "",
            "database": "snapshot",
            "port": 3306
        }
    )
    try:
        scraper.setup_driver()
        scraper.fetch_prefix_from_db()
        scraper.fetch_records_from_db()
        custom_output_dir = ""
        scraper.process_records()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        scraper.teardown()