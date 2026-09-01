# selenium_uploader.py

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


def upload_document(driver, title, file_path, notes):
    try:
        wait = WebDriverWait(driver, 15)

        # 1. Click "Upload Document"
        upload_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Upload Document')]"))
        )
        upload_button.click()

        # 2. Wait for modal
        wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "ui-dialog"))
        )

        # 3. Fill in the fields
        wait.until(EC.presence_of_element_located((By.NAME, "documentTitle"))).send_keys(title)
        driver.find_element(By.NAME, "file").send_keys(os.path.abspath(file_path))

        Select(driver.find_element(By.NAME, "documentType")).select_by_visible_text("CONSULTS")
        Select(driver.find_element(By.NAME, "provider")).select_by_visible_text("KLICKOVICH MD, ROBERT")

        driver.find_element(By.NAME, "notes").send_keys(notes)

        # 4. Submit
        driver.find_element(By.XPATH, "//button[normalize-space()='Upload']").click()

        print(f"✅ Uploaded: {os.path.basename(file_path)}")

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise
