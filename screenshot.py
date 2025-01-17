import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import os
import mariadb
import ftplib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YouTubeSearchScreenshot:
    def __init__(self, db_config, ftp_config, output_dir="screenshots"):
        self.base_url = "https://www.youtube.com/results"
        self.output_dir = output_dir
        self.driver = None
        self.db_config = db_config
        self.ftp_config = ftp_config
        self.records = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def setup_driver(self):
        """Set up the Chrome WebDriver using undetected_chromedriver."""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            #options.add_argument("--incognito")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            self.driver = uc.Chrome(options=options)
        except Exception as e:
            logging.error(f"Error setting up WebDriver: {e}")
            raise

    def fetch_records_from_db(self):
        """Fetch records from the database where screen_shot = TRUE."""
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            query = """
            SELECT 
                streams.id, 
                streams.search_query, 
                streams.keyword, 
                stream_metrics.title
            FROM 
                streams
            JOIN 
                stream_metrics 
            ON 
                stream_metrics.stream_id = streams.id
            WHERE 
                streams.snapshotted = FALSE
            """
            cursor.execute(query)
            self.records = cursor.fetchall()
            cursor.close()
            conn.close()
            logging.info(f"Fetched {len(self.records)} records from the database.")
        except mariadb.Error as e:
            logging.error(f"Error connecting to MariaDB: {e}")
            
    def update_record_status(self, record_id):
        """Update the record status to processed (TRUE) and set snapshot_url in the database."""
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            snapshot_url = f"{record_id}_{self.timestamp}_screenshot.png"
            query = """
            UPDATE streams 
            SET 
                snapshotted = TRUE, 
                snapshot_url = %s 
            WHERE 
                id = %s
            """
            cursor.execute(query, (snapshot_url, record_id))
            conn.commit()
            cursor.close()
            conn.close()
            logging.info(f"Record with ID {record_id} updated to processed with snapshot_url: {snapshot_url}.")
        except mariadb.Error as e:
            logging.error(f"Error updating record ID {record_id}: {e}")

    def navigate_to_search_results(self, search_query):
        """Navigate to the YouTube search results page."""
        try:
            self.driver.get(f"{self.base_url}?search_query={search_query}&gl=US")
            self.accept_terms_and_conditions()
            time.sleep(2)
            self.driver.get(f"{self.base_url}?search_query={search_query}&gl=US")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
        except Exception as e:
            logging.error(f"Error navigating to search results for query '{search_query}': {e}")

    def accept_terms_and_conditions(self):
        """Accept YouTube's terms and conditions if prompted."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='yt-spec-button-shape-next yt-spec-button-shape-next--filled yt-spec-button-shape-next--mono yt-spec-button-shape-next--size-m' and (@aria-label='Accept the use of cookies and other data for the purposes described' or @aria-label='Приемане на използването на „бисквитки“ и други данни за описаните цели')]"))
            ).click()
            logging.info("Accepted terms and conditions.")
        except Exception:
            logging.info("No terms and conditions prompt found.")

    def search_and_screenshot(self, record_id, title):
        """Search for the term on the page and capture a screenshot of the first result."""
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
                element = elements[0]
                self.driver.execute_script("arguments[0].style.border = '5px solid red';", element)
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(2)

                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                
                
                screenshot_path = os.path.join(self.output_dir, f"{record_id}_{self.timestamp}_screenshot.png")
                
                try:
                    self.driver.save_screenshot(screenshot_path)
                    logging.info(f"Screenshot saved at {screenshot_path}")
                except Exception as e:
                    logging.warning(f"Element screenshot failed, falling back to full-page screenshot: {e}")
                    return None
                    
                return screenshot_path
            else:
                logging.warning(f"Search term '{title}' not found on the page.")
                return None

        except Exception as e:
            logging.error(f"Error during search and screenshot for term '{title}': {e}")
            return None

    def upload_to_ftp(self, file_path):
        """Upload a file to the FTP server."""
        try:
            with ftplib.FTP(self.ftp_config['host']) as ftp:
                ftp.login(self.ftp_config['user'], self.ftp_config['password'])
                ftp.cwd(self.ftp_config['directory'])
                with open(file_path, 'rb') as file:
                    ftp.storbinary(f"STOR {os.path.basename(file_path)}", file)
            logging.info(f"Uploaded {file_path} to FTP.")
        except Exception as e:
            logging.error(f"Error uploading {file_path} to FTP: {e}")

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
            record_id, search_query, keyword, title = record
            self.navigate_to_search_results(search_query)
            screenshot_path = self.search_and_screenshot(record_id, title)
            if screenshot_path:
                self.upload_to_ftp(screenshot_path)
                self.update_record_status(record_id)

if __name__ == "__main__":
    scraper = YouTubeSearchScreenshot(
        db_config={
            "host": "",
            "user": "",
            "password": "",
            "database": "",
            "port": 3306
        },
        ftp_config={
            "host": "",
            "user": "",
            "password": "",
            "directory": ""
        }
    )
    try:
        scraper.setup_driver()
        scraper.fetch_records_from_db()
        scraper.process_records()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        scraper.teardown()
