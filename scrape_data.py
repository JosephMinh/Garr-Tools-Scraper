"""
Automated Tool Page PDF Printer - Custom Table Version
Handles expandable rows with "FULL DETAILS" buttons
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
import re
import sys
from tool_schemas import Tool, Series, ProductType, Products
from pydantic import ValidationError
from firecrawl import Firecrawl


##################################
# Playground for developing code snippets
##################################

PRODUCT_TYPES = [
    "Drills - High Performance",
    "Drills - General Purpose",
    "Reamers",
    "Drill Mills",
    "Roughers",
    "End Mills - High Performance",
    "End Mills - Stub Length",
    "End Mills - Standard Length",
    "End Mills - Extra Length",
    "Burrs/Rotary Files",
]
BASE_URL = "https://www.garrtool.com/"

def scrape_tool_details(driver, edp_number, series_name):
    """Scrape individual tool page and return Tool object"""
    # Click into tool page
    # Extract all fields
    list_info = driver.find_elements(
        By.XPATH,
        '//*[@id="post-397"]/div/div[2]/div[2]/div[1]/div[1]/ul[1]',
    )
    print(f" Scraped List Info: {list_info[0].text if list_info else 'N/A'}")
    series = driver.find_elements(
        By.XPATH,
        "/html/body/div[1]/main/form/div/div/div[1]/div[1]/strong",
    )
    print(f" Scraped Series Name: {series[0].text if series else 'N/A'}")
    regex = r"\d+(?:\.\d+)?xD"
    print(
        f"XD Extraction Result: {float(re.findall(regex, list_info[0].text, re.IGNORECASE)[0][:-2]) if list_info else None}"
    )
    tool = Tool(
        vendor_product_id=edp_number,
        series_name=series_name,
        xD=float(
            re.findall(r"\d+(?:\.\d+)?xD", list_info[0].text, re.IGNORECASE)[0][:-2]
        )
        if list_info
        else None,
    )
    print(f" Created Tool Object: {tool}")
    return tool

def scrape_tool_details_firecrawl(edp_number, series_name, product_url):
    """Scrape individual tool page and return Tool object"""
    # Click into tool page
    # Extract all fields
    app = Firecrawl(api_key="fc-f6dd17dfb285400b85b5002f1701962f")

    result = app.scrape(
        'https://www.garrtool.com/product-details/?EDP=70631',
        formats=[{
        "type": "json",
        "schema": Tool.model_json_schema(),
        "prompt": "Scrape all relevant fields for the tool on this page. Return a JSON object matching the Tool schema."
        }],
        only_main_content=False,
        timeout=120000
    )
    tool = Tool.model_validate(result)
    return tool

def scrape_series_table(driver, series_name):
    """Parse table and scrape all tools in series"""

    tools = []
    result_row_xpath = f'//div[@class="resultRow"]//strong[@class="name" and contains(text(), "{series_name}")]'
    series_element = driver.find_element(By.XPATH, result_row_xpath)
    result_row = series_element.find_element(
        By.XPATH, './ancestor::div[@class="resultRow"]'
    )

    # Find the product-table within this resultRow
    product_table = result_row.find_element(By.CSS_SELECTOR, "ul.product-table")

    # Get the data-id of this table for reference
    table_id = product_table.get_attribute("data-id")

    # Find all rows within this specific table
    # <li data-id="12641" class="series-results-row">
    rows = product_table.find_elements(By.CSS_SELECTOR, "li.series-results-row")
    print(f"Found {len(rows)} rows in series '{series_name}'")
    edp_numbers = []
    count = 0
    for row in rows:
        edp_number = get_edp_from_row(row)
        if edp_number:
            edp_numbers.append(edp_number)
            count += 1
        if count >= 10:
            break
    print(f"Found {len(edp_numbers)} EDP numbers in series '{series_name}'")
    for edp_number in edp_numbers:
        try:
            driver.get(f"https://www.garrtool.com/product-details/?EDP={edp_number}")
            time.sleep(2)  # Wait for page to load
            # Scrape tool details
            try:
                print(f"  Scraping tool EDP {edp_number}...")
                tool = scrape_tool_details(driver, edp_number, series_name)
                tools.append(tool)

            except ValidationError as ve:
                print(f"  ✗ Validation error for EDP {edp_number}: {str(ve)}")

        except Exception as e:
            print(f"  ✗ Error navigating to EDP {edp_number}: {str(e)}")

    series = Series(
        name=series_name,
        details="...",  # Extract from page
        tolerances="...",  # Extract from page
        tools=tools,
    )
    return series


def scrape_product_type(driver, actions, product_type_name):
    """Navigate to product type and scrape all series"""
    # Navigate to product type page
    try:
        # Click all "Load All Series Results" buttons
        go_to_product_table_page(driver, BASE_URL, actions, link_text=product_type_name)
        product_type_url = driver.current_url

    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()

    serieses = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "strong.name"))
    )
    series_names = [series.text.split("\n", 1)[0] for series in serieses]

    series_list = []
    for i, series_name in enumerate(series_names):
        print(f"Scraping series: {series_name}")
        expand_table(driver, actions, i)
        series_list.append(scrape_series_table(driver, series_name))
        print(series_list)
        driver.get(product_type_url)
        time.sleep(2)
        if i >= 2:
            break
    # return series_list
    return ProductType(name=product_type_name, series=series_list)


def expand_table(driver, actions, table_number):
    """Expand all series tables by clicking 'Load All Series Results' buttons"""

    try:
        load_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.PARTIAL_LINK_TEXT, "Load All Series Results")
            )
        )
        print(f"Found {len(load_buttons)} 'Load All Series Results' buttons")

        if load_buttons:
            button = load_buttons[table_number]
            button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
            actions.scroll_to_element(button).perform()
            # Use JavaScript click as fallback
            driver.execute_script("arguments[0].click();", button)

        if not load_buttons:
            print("No 'Load All Series Results' buttons found")
        time.sleep(1)
    except Exception as e:
        print(f"No more buttons found or error: {e}")
    print("All series tables expanded.")


###################################


def setup_chrome_driver(output_folder):
    """Configure Chrome driver with PDF printing capabilities"""
    chrome_options = Options()

    # Set download preferences for PDF
    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps(
            {
                "recentDestinations": [
                    {"id": "Save as PDF", "origin": "local", "account": ""}
                ],
                "selectedDestinationId": "Save as PDF",
                "version": 2,
            }
        ),
        "savefile.default_directory": output_folder,
        "download.default_directory": output_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--kiosk-printing")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(1)
    return driver


def go_to_product_table_page(driver, url, actions, link_text):
    """Navigate to the product table page"""
    # Navigate to main page
    driver.get(url)
    time.sleep(2)  # Wait for page load

    # Hover over the products button to reveal the submenu
    products_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "PRODUCTS"))
    )

    actions.move_to_element(products_button).perform()
    time.sleep(1)
    # Click on "Drills - General Purpose"
    drills_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, link_text))
    )
    drills_button.click()
    time.sleep(2)


def get_all_product_rows(driver):
    """Find all product rows (li elements with series-results-row class)"""
    wait = WebDriverWait(driver, 10)

    try:
        # Wait for the product table to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-table")))

        # Find all li elements that contain product data
        # Based on the HTML: <li data-id="1011" class="series-results-row">
        rows = driver.find_elements(By.CSS_SELECTOR, "li.series-results-row")

        print(f"Found {len(rows)} product rows")
        return rows
    except TimeoutException:
        print("Error: Could not find product table")
        return []


def get_edp_from_row(row):
    """Extract EDP number from a row element"""
    try:
        # Look for the EDP link inside <strong class="title srEDP">
        # <a href="#" data-id="90275" class="open">90275</a>
        edp_link = row.find_element(By.CSS_SELECTOR, "strong.srEDP a.open")
        edp_number = str(edp_link.text.strip())
        return edp_number
    except NoSuchElementException:
        return None


def expand_row_and_click_details(driver, row, edp_number):
    """
    Expand a row by clicking the EDP link, then click FULL DETAILS button
    Returns True if successful, False otherwise
    """
    try:
        # Step 1: Click on the EDP link to expand the row
        edp_link = row.find_element(By.CSS_SELECTOR, "strong.srEDP a.open")

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView(true);", edp_link)
        time.sleep(0.5)

        # Click to expand
        print(f"  Expanding row for EDP {edp_number}...")
        driver.execute_script("arguments[0].click();", edp_link)
        # edp_link.click()
        time.sleep(1)  # Wait for expansion animation
        print(f"  Row expanded.")
        # Step 2: Find and click the "FULL DETAILS" button
        # The button should now be visible in the expanded content
        wait = WebDriverWait(driver, 5)
        print(f"Creating selectors for FULL DETAILS button...")
        # Try multiple possible selectors for the FULL DETAILS button
        selectors = [
            "a:contains('FULL DETAILS')",  # Won't work in Selenium
            "//a[contains(text(), 'FULL DETAILS')]",  # XPath
            "a[href*='FULL']",
            ".full-details-btn",
            "a.button:contains('FULL')",
        ]
        print(f"  Locating FULL DETAILS button...")
        # Use XPath as it's most reliable for text matching
        full_details_btn = wait.until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "FULL DETAILS"))
        )

        print(f"  Clicking FULL DETAILS button...")
        driver.execute_script("arguments[0].click();", full_details_btn)

        # full_details_btn.click()
        time.sleep(2)  # Wait for page to load

        return True

    except TimeoutException:
        print(f"  ✗ FULL DETAILS button for EDP {edp_number}")
        return False
    except NoSuchElementException as e:
        print(f"  ✗ Could not find element for EDP {edp_number}: {str(e)}")
        return False
    except Exception as e:
        print(f"  ✗ Error processing EDP {edp_number}: {str(e)}")
        return False


def print_page_to_pdf(driver, filename):
    """Print current page to PDF"""
    try:
        # Execute Chrome's print command
        result = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "landscape": True,  # Landscape for wide tables
                "paperWidth": 11,
                "paperHeight": 8.5,
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
                "scale": 0.9,
            },
        )

        # Decode and save PDF
        import base64

        with open(filename, "wb") as f:
            f.write(base64.b64decode(result["data"]))

        print(f"  ✓ Saved: {os.path.basename(filename)}")
        return True
    except Exception as e:
        print(f"  ✗ Error printing PDF: {str(e)}")
        return False


def main():
    output_folder = os.path.join(os.getcwd(), "tool_pdfs")
    driver = setup_chrome_driver(output_folder)
    actions = ActionChains(driver)
    product_types = []
    for i, product_type_name in enumerate(PRODUCT_TYPES):
        product_type = scrape_product_type(driver, actions, product_type_name)
        product_types.append(product_type)
        print(product_types)
        if i >= 1:
            break

    products = Products(types=product_types)
    print(products.model_dump_json(indent=2))
    with open("garr_products.json", "w", encoding="utf-8") as f:
        f.write(products.model_dump_json(indent=2))

    driver.quit()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("=" * 60)
    print("=" * 60 + "\n")

    response = input("Ready to start? (y/n): ")
    if response.lower() == "y":
        main()
    else:
        print("Cancelled.")
