# pip install selenium pandas openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

import pandas as pd
import re
from datetime import datetime
import time

INPUT_XLSX = "product_data.xlsx"              # your uploaded file name
PINCODE = "110028"                            # change if needed
OUTPUT_XLSX = f"blinkit_scrapped_sheet_{datetime.now().strftime('%d-%m-%Y--%H-%M')}.xlsx"  # new file to be created
OUTPUT_SHEET = "blinkit_scrapped_sheet"

# ---------- Helpers ----------
def make_driver(headless=False):
    chrome_opts = Options()
    # comment these if you want to see the browser
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--start-maximized")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--window-size=1440,900")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_opts)
    driver.set_page_load_timeout(60)
    return driver

def set_location(driver, pincode):
    driver.get("https://blinkit.com/")
    wait = WebDriverWait(driver, 20)
    # click the location input
    loc_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="search delivery location"]')))
    loc_input.clear()
    loc_input.send_keys(pincode)

    # pick first suggestion
    suggestion = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"LocationSearchList__LocationDetailContainer")]')))
    suggestion.click()

    # wait for homepage to stabilize (search bar visible)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"SearchBar__AnimationWrapper")]')))

def open_url_and_get_price(driver, url):
    """Open product URL directly and try to read the price on PDP."""
    wait = WebDriverWait(driver, 20)
    driver.get(url)

    # Possible price locators on Blinkit PDP (keep a few fallbacks)
    price_locators = [
        # PDP price container variations (class names often change; keep multiple robust options)
        (By.XPATH, '//*[contains(@class,"SellingPrice") or contains(@class,"sellingPrice") or contains(@class,"Price")][1]'),
        (By.XPATH, '//*[self::div or self::span][contains(text(),"₹")][1]'),
        (By.XPATH, '//span[contains(@class,"rupee") or contains(text(),"₹")][1]')
    ]

    for how, what in price_locators:
        try:
            el = wait.until(EC.presence_of_element_located((how, what)))
            txt = el.text.strip()
            price = extract_price(txt)
            if price:
                return price
        except TimeoutException:
            continue
        except StaleElementReferenceException:
            continue

    # If not found in the above, try to peek at the "ADD" card area on PDP (sometimes same layout as listing)
    try:
        card = driver.find_element(By.XPATH, '//*[contains(@class,"AddToCart") or contains(., "ADD")]')
        txt = card.text
        price = extract_price(txt)
        if price:
            return price
    except NoSuchElementException:
        pass

    return None

def search_title_and_get_price(driver, title):
    """Use the site search, pick the best-matching card that has ADD button, and read its price."""
    wait = WebDriverWait(driver, 20)

    # Focus the search input
    search_wrap = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"SearchBar__AnimationWrapper")]')))
    search_wrap.click()
    search_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@class,"SearchBarContainer__Input")]')))

    # clear previous query
    search_input.send_keys(Keys.CONTROL, "a")
    search_input.send_keys(Keys.DELETE)
    search_input.send_keys(title)
    # allow results to load
    time.sleep(2.0)

    # product cards in search results
    # Use a broad container selector; your original code used 'categories-table'
    cards = driver.find_elements(By.XPATH, '//div[contains(@class,"categories-table")]/div/div | //div[contains(@class,"Product") or contains(@class,"CategoryProduct")]')

    if not cards:
        # slight fallback wait then re-query
        time.sleep(1.5)
        cards = driver.find_elements(By.XPATH, '//div[contains(@class,"categories-table")]/div/div | //div[contains(@class,"Product") or contains(@class,"CategoryProduct")]')

    best_price = None
    best_score = -1

    for card in cards:
        try:
            text = card.text.strip()
            if not text or "ADD" not in text:
                continue

            # split like your original approach: [Delivery Time, Product Name, Quantity, Price, ...]
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            # Guess fields conservatively
            name = None
            price_text = None

            # Try to pick the first ₹-looking token as price, and a non-₹ line as name
            for p in parts:
                if "₹" in p or re.search(r'\b[0-9]+\b', p) and "ADD" not in p and "OFF" not in p and "MIN" not in p:
                    # keep all potential price lines; we'll extract properly
                    if extract_price(p):
                        price_text = p
                # Treat a line without ₹/ADD/OFF/MIN that is reasonably texty as product name
            # crude heuristic for name
            candidates = [p for p in parts if ("₹" not in p and "ADD" not in p and "OFF" not in p and "MIN" not in p and len(p) > 2)]
            if candidates:
                name = candidates[0]
            if price_text is None:
                # sometimes price is the 3rd or 4th line like your code
                price_text = parts[3] if len(parts) > 3 else None

            price_val = extract_price(price_text) if price_text else None
            if not price_val:
                continue

            # score by fuzzy containment
            score = title_similarity(title, name or "")
            if score > best_score:
                best_score = score
                best_price = price_val
        except Exception:
            continue

    return best_price

def extract_price(text):
    if not text:
        return None
    # find ₹-style price or digits with optional decimal
    m = re.search(r'₹\s*([0-9][0-9,]*\.?[0-9]*)', text)
    if not m:
        m = re.search(r'\b([0-9][0-9,]*\.?[0-9]*)\b', text)
    if not m:
        return None
    val = m.group(1).replace(",", "")
    try:
        return float(val)
    except ValueError:
        return None

def title_similarity(a, b):
    if not a or not b:
        return 0
    a = a.lower()
    b = b.lower()
    # simple token overlap
    at = set(re.findall(r'\w+', a))
    bt = set(re.findall(r'\w+', b))
    if not at or not bt:
        return 0
    return len(at & bt) / len(at)

# ---------- Main ----------
def run():
    df = pd.read_excel(INPUT_XLSX)  # expects columns: 'Sku Code', 'Product Name', 'Blinkit'
    out_rows = []

    driver = make_driver(headless=False)  # set True if you want headless
    try:
        set_location(driver, PINCODE)

        for idx, row in df.iterrows():
            # breakpoint()  # for debugging, remove in production
            sku = str(row.get("Sku Code", "")).strip()
            title = str(row.get("Product Name", "")).strip()
            url = str(row.get("Blinkit", "")).strip()
            price = None
            source = None

            # Prefer URL when present
            if url and url.lower().startswith("http"):
                price = open_url_and_get_price(driver, url)
                source = "url"

            # Fallback to search by title
            if price is None and title:
                price = search_title_and_get_price(driver, title)
                source = "search"

            out_rows.append({
                "SKU Code": sku,
                "Title": title,
                "Product Url": url,
                "Product Price": price,
                # "Source": source
            })
            print(f"[{idx+1}/{len(df)}] {sku} | {title} -> {price} ({source})")

        out_df = pd.DataFrame(out_rows)
        # save with requested sheet name
        with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
            out_df.to_excel(writer, sheet_name=OUTPUT_SHEET, index=False)
        print(f"Saved: {OUTPUT_XLSX} (sheet: {OUTPUT_SHEET})")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
