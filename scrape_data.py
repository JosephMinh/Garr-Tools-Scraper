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
import sys
from tool_schemas import Tool, Series, ProductType, Products
from pydantic import ValidationError

##################################
# Playground for developing code snippets
##################################

PRODUCT_TYPES = [
"Drills - High Performance"
"Drills - General Purpose"
"Reamers",
"Drill Mills",
"Roughers",
"End Mills - High Performance",
"End Mills - Stub Length",
"End Mills - Standard Length",
"End Mills - Extra Length",
"Burrs/Rotary Files"
]

def scrape_tool_details(edp_number, series_name, product_url):
    """Scrape individual tool page and return Tool object"""
    # Click into tool page
    # Extract all fields
    tool = Tool(
        vendor_product_id=edp_number,
        series_name=series_name,
        product_url=product_url,
        diameter=extracted_diameter,
        flute_count=extracted_flutes,
        # ... etc
        attributes_json={
            "neck_diameter": extracted_neck_diameter,
            "neck_length_behind_flutes": extracted_neck_length,
            "corner_radius": extracted_corner_radius,
            "end_type": extracted_end_type,
            "flat": extracted_flat,
            "weight": extracted_weight
        }
    )
    return tool

def scrape_series_table(driver, series_name):
    """Parse table and scrape all tools in series"""
    tools = []
    result_row_xpath = f'//div[@class="resultRow"]//strong[@class="name" and contains(text(), "{series_name}")]'
    series_element = driver.find_element(By.XPATH, result_row_xpath)
    result_row = series_element.find_element(By.XPATH, './ancestor::div[@class="resultRow"]')

    # Find the product-table within this resultRow
    product_table = result_row.find_element(By.CSS_SELECTOR, 'ul.product-table')

    # Get the data-id of this table for reference
    table_id = product_table.get_attribute('data-id')

    # Find all rows within this specific table
    # <li data-id="12641" class="series-results-row">
    rows = product_table.find_elements(By.CSS_SELECTOR, 'li.series-results-row')
    edp_numbers = []
    for row in rows:
        edp_number = get_edp_from_row(row)
        edp_numbers.append(edp_number)
        
    for edp_number in edp_numbers:
            try:
                driver.get(
                    f"https://www.garrtool.com/product-details/?EDP={edp_number}"
                )
                time.sleep(2)  # Wait for page to load
                # Scrape tool details
                try:
                    tool = scrape_tool_details(
                        edp_number, series_name, driver.current_url
                    )
                    tools.append(tool)
                    print(f"  ✓ Scraped tool EDP {edp_number}")
                    
                except ValidationError as ve:
                    print(f"  ✗ Validation error for EDP {edp_number}: {str(ve)}")
                
            except Exception as e:
                print(f"  ✗ Error navigating to EDP {edp_number}: {str(e)}")
                fail_count += 1
    
    series = Series(
        name=series_name,
        details="...",  # Extract from page
        tolerances="...",  # Extract from page
        tools=tools
    )
    return series

def scrape_product_type(driver, product_type_name):
    """Navigate to product type and scrape all series"""
    # Navigate to product type page
    try:
        # Click all "Load All Series Results" buttons
        go_to_product_table_page(
            driver, base_url, actions, link_text="Drills - General Purpose"
        )
        while True:
            try:
                load_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.PARTIAL_LINK_TEXT, "Load All Series Results")
                    )
                )
                print(f"Found {len(load_buttons)} 'Load All Series Results' buttons")

                if load_buttons:
                    for button in load_buttons:
                        button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(button)
                        )
                        actions.scroll_to_element(button).perform()
                        # Use JavaScript click as fallback
                        driver.execute_script("arguments[0].click();", button)
                        load_buttons = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.PARTIAL_LINK_TEXT, "Load All Series Results")
                            )
                        )

                if not load_buttons:
                    break
                time.sleep(1)
            except Exception as e:
                print(f"No more buttons found or error: {e}")
                break

        print("Scraping completed successfully")
        time.sleep(3)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()

    serieses = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "strong.name")
                    )
                )
    series_list = [series.text.split('\n', 1)[0] for series in serieses]
    
    
    return ProductType(name=product_type_name, series=series_list)

product_type = scrape_product_type(driver, "Drills - General Purpose")
