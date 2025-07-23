from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def upload_pdf_to_portal(pdf_path: str, date_of_eval: str):
    URL = "https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # remove this line if you want to see the browser
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(URL)

        wait = WebDriverWait(driver, 15)

        # Click "Upload Document" button if necessary (depends on site behavior)

        # Fill out Document Title
        doc_title = f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {date_of_eval}"
        wait.until(EC.presence_of_element_located((By.NAME, "documentTitle"))).send_keys(doc_title)

        # Upload PDF file
        wait.until(EC.presence_of_element_located((By.NAME, "uploadedfile"))).send_keys(pdf_path)

        # Select Document Type
        doc_type_dropdown = Select(wait.until(EC.presence_of_element_located((By.NAME, "documentType"))))
        doc_type_dropdown.select_by_visible_text("Consults")

        # Select Provider
        provider_dropdown = Select(wait.until(EC.presence_of_element_located((By.NAME, "provider"))))
        provider_dropdown.select_by_visible_text("KLICKOVICH MD, ROBERT")

        # Fill out Notes
        wait.until(EC.presence_of_element_located((By.NAME, "notes"))).send_keys(doc_title)

        # Submit (adjust button locator if necessary)
        submit_button = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="submit" or @value="Upload"]')))
        submit_button.click()

        print(f"✅ Successfully uploaded PDF: {pdf_path}")

    except Exception as e:
        print("❌ Upload failed:", str(e))
    finally:
        time.sleep(3)  # Wait for any finalization
        driver.quit()
