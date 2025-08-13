# 🛒 Blinkit Product Price Scraper
A Python-based Selenium scraper that:
---

Reads a list of Blinkit products from an Excel file (product_data.xlsx).
Sets the delivery location using a given PIN code.
For each product:

If a product URL is available, opens it directly to fetch the price.
Otherwise, searches for the product name and fetches the price from the search results.
Saves the results into a new Excel file with the format:
📂 Project Structure
├── product_data.xlsx # Input file with SKU, Product Name, Blinkit URL
├── blinkit_scraper.py # Main scraper script
├── requirements.txt # Python dependencies
└── README.md # Documentation

## 📁 Folder Structure

```
Data-Scrapper/
│
├── product_data.xlsx           # Input file with SKU, Product Name, Blinkit URL
├── blinkit_scraper.py          # Main scraper script
└── README.md                   # Documentation (this file)
```

📦 Requirements
---
    - Python 3.8+
    - Google Chrome (latest version)
    - ChromeDriver (matching your Chrome version) — Selenium 4 can auto-manage this.
    - Internet connection (Blinkit is an online platform).
    - Python Libraries
    - selenium
    - pandas
    - openpyxl



📑 Input File Format (product_data.xlsx) The Excel must contain exactly these columns:

### Check `product_data.xlsx`
Update the spreadsheet with product SKUs and URLs under each store's column:

| Sku Code | Product Name  | Product Url |
|----------|------------|-------------|
| GC990    | Lamel All in on...| https://... |


### ⚙ How It Works (Overview)
Set Delivery Location: Opens Blinkit, enters your PIN code, selects the first suggestion.
- Loop Products: - If Blinkit URL exists → opens PDP (product page) → extracts price.
- Else uses Product Name → searches → picks best match → extracts price. Save Output: 

Creates an Excel file named like blinkit_scrapped_sheet_13-08-2025--13-08.xlsx with columns:

- SKU
- Title
- Price Url
- Product Price

🚀 Usage Run the script from the project directory:

```
python blinkit_scraper.py
```
📝 Configuration Snippets
Set the output filename pattern (current date + time):


   ```
   from datetime import datetime
   OUTPUT_XLSX = f"blinkit_scrapped_sheet_{datetime.now().strftime('%d-%m-%Y--%H-%M')}.xlsx"
   ```
Set your PIN code and (optional) headless mode:


```
PINCODE = "110028 (default one)"
driver = make_driver(headless=True)  # set False to watch the browser

```
### ⚔️ Limitations for Me:
 - Blinkit’s HTML/CSS may change. If prices stop appearing, update the XPath/CSS selectors in the script.
 - Ensure Chrome and ChromeDriver are compatible (Selenium 4 usually manages this automatically).
 - Respect website Terms of Service. This project is for educational purposes only


 
## 💡 Tips

- Don't run scraping in parallel too fast — add delays
- Log everything with `logging.info()` and `logging.error()`
- Check `scraper.log` and HTML for troubleshooting

---

## 📬 Author & Support

- Built by Lalit Thapa
- For help, raise an issue or ping me on lalitthapa2108@gmail.com or +91 9871776722

---

## 📜 License
MIT License. Free to use for personal and commercial use.

---

## 📌 Example Output

| Sku Code | Product Name | Url | Price  |
|----------|------------|-------------|-------------|
| GC990    | Lamel All in o...      | https://www.blinkit.com/l/p..        | ₹716    |

---

Enjoy tracking your product prices effortlessly! 🛍️
