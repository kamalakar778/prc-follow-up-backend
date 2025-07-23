import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os

def upload_pdf_to_portal(file_path: str, document_title: str, notes: str = ""):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Connect to existing Chrome with remote debugging
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
        wait = WebDriverWait(driver, 20)

        print("✅ Connected to existing Chrome window")

        # Switch to correct tab (should already be on patient_doc.jsp)
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp")

        # Wait for and click the Upload Document option
        upload_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Upload Document')]")))
        upload_button.click()

        # Wait for the document title input
        title_input = wait.until(EC.presence_of_element_located((By.NAME, "docTitle")))
        title_input.clear()
        title_input.send_keys(document_title)

        # Upload the PDF file
        file_input = wait.until(EC.presence_of_element_located((By.NAME, "uploadFile")))
        file_input.send_keys(file_path)

        # Select document type: "Consults"
        doc_type_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "docType")))
        for option in doc_type_dropdown.find_elements(By.TAG_NAME, 'option'):
            if option.text.strip().lower() == "consults":
                option.click()
                break

        # Select provider: "KLICKOVICH MD, ROBERT"
        provider_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "providerId")))
        for option in provider_dropdown.find_elements(By.TAG_NAME, 'option'):
            if "KLICKOVICH" in option.text.upper():
                option.click()
                break

        # Enter notes
        notes_input = wait.until(EC.presence_of_element_located((By.NAME, "docNote")))
        notes_input.clear()
        notes_input.send_keys(notes)

        # Submit
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Upload']")))
        submit_button.click()

        print("✅ Upload completed for:", file_path)

    except Exception as e:
        print("❌ Upload failed:", e)
        raise

    finally:
        # Do not close browser (user wants to keep it open)
        pass
