import os
import glob
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

# Constants
PROVIDER_NAME = "KLICKOVICH MD, ROBERT"
DOCUMENT_TYPE = "Consults"
UPLOAD_URL = "https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp"


def get_driver():
    options = Options()
    
    # Optional: Use user profile to retain login
    user_profile = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\ww.Kamlakar")
    if os.path.exists(user_profile):
        options.add_argument(f"user-data-dir={user_profile}")
        options.add_argument("profile-directory=ww.Kamlakar")

    # Silent mode (optional)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    return webdriver.Chrome(options=options)


def click_upload_document(driver):
    wait = WebDriverWait(driver, 20)
    print("[Selenium] Waiting for 'Upload Document' button...")
    upload_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[contains(@src, 'doc_upload.gif')]")))
    upload_button.click()
    print("[Selenium] Clicked 'Upload Document'.")


def handle_possible_alert(driver):
    try:
        alert = driver.switch_to.alert
        print("[Selenium] ALERT FOUND:", alert.text)
        alert.accept()
    except NoAlertPresentException:
        pass


def confirm_upload_success(driver):
    try:
        WebDriverWait(driver, 5).until(EC.invisibility_of_element((By.NAME, "documentPath")))
        print("[Selenium] Upload likely succeeded.")
        return True
    except TimeoutException:
        print("[Selenium] Upload failed or form is still visible.")
        return False


def upload_document(driver, title, file_path):
    try:
        wait = WebDriverWait(driver, 20)
        print("[Selenium] Waiting for upload form...")
        wait.until(EC.presence_of_element_located((By.NAME, "documentTitle")))

        print(f"[Selenium] Filling form for: {title}")
        driver.find_element(By.NAME, "documentTitle").clear()
        driver.find_element(By.NAME, "documentTitle").send_keys(title)

        print(f"[Selenium] Selecting file: {file_path}")
        driver.find_element(By.NAME, "documentPath").send_keys(file_path)

        print("[Selenium] Selecting Document Type and Provider...")
        Select(driver.find_element(By.NAME, "docType")).select_by_visible_text(DOCUMENT_TYPE)
        Select(driver.find_element(By.NAME, "providerId")).select_by_visible_text(PROVIDER_NAME)

        driver.find_element(By.NAME, "notes").clear()
        driver.find_element(By.NAME, "notes").send_keys(title)

        print("[Selenium] Submitting the form...")
        driver.find_element(By.NAME, "submit").click()

        WebDriverWait(driver, 5).until(EC.staleness_of(driver.find_element(By.NAME, "submit")))
        handle_possible_alert(driver)
        return confirm_upload_success(driver)

    except Exception as e:
        print(f"[Selenium] Error during document upload: {e}")
        return False


def find_pdf_by_prefix(folder, prefix):
    """Find the first PDF file in the folder that starts with the given prefix."""
    pattern = os.path.join(folder, f"{prefix}*.pdf")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def upload_both_files(date_of_evaluation, raw_folder_path, raw_file_name, transcribed_folder_path, transcribed_file_name):
    print("[Upload] Starting upload_both_files()...")
    driver = get_driver()

    try:
        raw_file_path = find_pdf_by_prefix(raw_folder_path, raw_file_name)
        transcribed_file_path = find_pdf_by_prefix(transcribed_folder_path, transcribed_file_name)

        if not raw_file_path:
            print(f"[Error] RAW file starting with '{raw_file_name}' not found in {raw_folder_path}")
            return
        if not transcribed_file_path:
            print(f"[Error] TRANSCRIBED file starting with '{transcribed_file_name}' not found in {transcribed_folder_path}")
            return

        # Upload RAW
        driver.get(UPLOAD_URL)
        click_upload_document(driver)
        raw_title = f"RAW DATA FOLLOW UP VISIT NOTE ON {date_of_evaluation}"
        success_raw = upload_document(driver, raw_title, raw_file_path)

        # Upload TRANSCRIBED
        driver.get(UPLOAD_URL)
        click_upload_document(driver)
        transcribed_title = f"TRANSCRIBED DATA FOLLOW UP VISIT NOTE ON {date_of_evaluation}"
        success_transcribed = upload_document(driver, transcribed_title, transcribed_file_path)

        print("[Upload] Upload complete.")
        if success_raw and success_transcribed:
            print("[Upload] ✅ Both files uploaded successfully.")
        elif not success_raw:
            print("[Upload] ❌ RAW file upload failed.")
        elif not success_transcribed:
            print("[Upload] ❌ Transcribed file upload failed.")
    finally:
        driver.quit()
