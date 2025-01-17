# Snapshot Bot README

## Overview

**Snapshot Bot** is a Python-based application designed to automate the process of capturing screenshots of YouTube search results. This bot integrates Selenium with the `undetected_chromedriver` library to navigate YouTube, fetch search results, highlight specific videos, take screenshots, and upload them to an FTP server. It also interacts with a MariaDB database to manage records and update statuses.

---

## Features

- **Database Integration**: Fetches records from a MariaDB database and updates processed records with screenshot URLs.
- **YouTube Search Automation**: Navigates to YouTube, performs search queries, and highlights target videos.
- **Screenshot Capture**: Captures and stores screenshots locally.
- **FTP Upload**: Uploads screenshots to an FTP server for external access.
- **Headless Browsing**: Operates in a headless mode for efficiency and seamless automation.

---

## Prerequisites

- Python 3.8 or later
- MariaDB
- FTP server for storing screenshots

---

## Dependencies

Install the required dependencies using pip:

```bash
pip install selenium undetected-chromedriver mariadb
```

---

## Configuration

1. **Database Configuration**: Provide your MariaDB details in the `db_config` dictionary:
   ```python
   db_config = {
       "host": "your_database_host",
       "user": "your_database_user",
       "password": "your_database_password",
       "database": "your_database_name",
       "port": 3306
   }
   ```

2. **FTP Configuration**: Set your FTP server credentials in the `ftp_config` dictionary:
   ```python
   ftp_config = {
       "host": "your_ftp_host",
       "user": "your_ftp_user",
       "password": "your_ftp_password",
       "directory": "your_ftp_directory"
   }
   ```

3. **Output Directory**: Screenshots are stored locally in the `screenshots` folder by default.

---

## How It Works

1. **Setup**: Initializes the Chrome WebDriver using `undetected_chromedriver` to avoid detection.
2. **Fetch Records**: Retrieves unprocessed records from the database.
3. **YouTube Search**: Automates YouTube searches for specific queries and highlights relevant results.
4. **Capture Screenshot**: Takes screenshots of highlighted search results.
5. **Upload to FTP**: Uploads the captured screenshot to the FTP server.
6. **Update Database**: Updates the record status and snapshot URL in the database.

---

## Usage

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/snapshot-bot.git
   cd snapshot-bot
   ```

2. Run the script:
   ```bash
   python snapshot_bot.py
   ```

3. Monitor logs for detailed execution progress.

---

## Logging

Logs are configured to display important events and errors in the following format:
```plaintext
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```

---

## Example Database Schema

Here’s a simplified example of the database schema:

**`streams` Table**
| Column         | Type       | Description                     |
|----------------|------------|---------------------------------|
| id             | INT        | Primary Key                    |
| search_query   | VARCHAR    | YouTube search query           |
| keyword        | VARCHAR    | Keyword to identify records    |
| snapshotted    | BOOLEAN    | Snapshot status (default FALSE) |
| snapshot_url   | VARCHAR    | URL of the uploaded screenshot |

**`stream_metrics` Table**
| Column     | Type  | Description                   |
|------------|-------|-------------------------------|
| stream_id  | INT   | Foreign key to `streams`      |
| title      | TEXT  | Video title for highlighting |

---

## Error Handling

- **WebDriver Errors**: Logs detailed error messages if the driver setup fails.
- **Database Errors**: Ensures database connections are closed properly after errors.
- **Screenshot Errors**: Falls back to full-page screenshots if element-level screenshots fail.
- **FTP Errors**: Logs any issues during file uploads.

---

## License

This project is open-source and available under the [MIT License](LICENSE).

---

Feel free to customize this template further to suit your project structure or specific requirements!
