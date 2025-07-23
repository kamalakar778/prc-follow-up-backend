import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ IMPORTANT:
# Make sure Chrome is launched manually using this exact .bat file:
# @echo off
# start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
# --remote-debugging-port=9222 ^
# --user-data-dir="C:\Users\kamal\AppData\Local\Google\Chrome\User Data" ^
# --profile-directory="Default"

def get_driver():
    """Attach to manually launched Chrome with remote debugging."""
    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    return webdriver.Chrome(options=options)

def wait_for_element(driver, by, value, timeout=15):
    """Wait for an element to be present in the DOM."""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except Exception as e:
        raise RuntimeError(f"❌ Timeout waiting for element '{value}': {e}")

def upload_file_with_ui_controls(driver, title, file_path, doc_type, provider, notes):
    """Fill out and submit the document upload form."""
    print(f"\n📤 Uploading: {title}")
    
    wait_for_element(driver, By.NAME, "title").clear()
    driver.find_element(By.NAME, "title").send_keys(title)
    driver.find_element(By.NAME, "document").send_keys(file_path)

    # Select document type
    doc_type_select = driver.find_element(By.NAME, "documentType")
    matched = False
    for option in doc_type_select.find_elements(By.TAG_NAME, "option"):
        if option.text.strip().lower() == doc_type.lower():
            option.click()
            matched = True
            break
    if not matched:
        raise ValueError(f"❌ Document type '{doc_type}' not found in dropdown.")

    # Select provider
    provider_select = driver.find_element(By.NAME, "provider")
    matched = False
    for option in provider_select.find_elements(By.TAG_NAME, "option"):
        if option.text.strip().lower() == provider.lower():
            option.click()
            matched = True
            break
    if not matched:
        raise ValueError(f"❌ Provider '{provider}' not found in dropdown.")

    driver.find_element(By.NAME, "note").clear()
    driver.find_element(By.NAME, "note").send_keys(notes)

    time.sleep(1)
    driver.find_element(By.NAME, "uploadButton").click()
    print(f"✅ Uploaded: {title}")

def upload_both_files(date_of_evaluation: str, raw_file_path: str, transcribed_file_path: str):
    """Upload both RAW and TRANSCRIBED PDF files using the open Chrome session."""
    print(f"\n🔍 Checking RAW path: {raw_file_path}")
    print(f"🔍 Checking TRANSCRIBED path: {transcribed_file_path}")

    if not os.path.isfile(raw_file_path):
        raise FileNotFoundError(f"❌ Raw file not found: {raw_file_path}")
    if not os.path.isfile(transcribed_file_path):
        raise FileNotFoundError(f"❌ Transcribed file not found: {transcribed_file_path}")

    print("🚀 Connecting to Chrome via debugger...")
    driver = get_driver()

    print("🌐 Navigating to upload page...")
    driver.get("https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp")
    wait_for_element(driver, By.NAME, "title")

    # Upload RAW document
    upload_file_with_ui_controls(
        driver,
        title=f"RAW - {date_of_evaluation}",
        file_path=raw_file_path,
        doc_type="Consults",
        provider="KLICKOVICH MD, ROBERT",
        notes="Raw audio result"
    )

    time.sleep(2)

    # Upload TRANSCRIBED document
    upload_file_with_ui_controls(
        driver,
        title=f"TRANSCRIBED - {date_of_evaluation}",
        file_path=transcribed_file_path,
        doc_type="Consults",
        provider="KLICKOVICH MD, ROBERT",
        notes="Transcribed document"
    )

    print("\n✅ Both files uploaded successfully.")
