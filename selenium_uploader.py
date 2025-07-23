from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import os

def upload_document(driver, title, file_path, notes):
    try:
        # 1. Click "Upload Document"
        upload_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Upload Document')]"))
        )
        upload_button.click()

        # 2. Wait for modal to appear
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'ui-dialog')]"))
        )

        # 3. Fill in the fields
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        driver.find_element(By.XPATH, "//input[@type='text' and @name='documentTitle']").send_keys(title)

        driver.find_element(By.XPATH, "//input[@type='file']").send_keys(os.path.abspath(file_path))

        Select(driver.find_element(By.XPATH, "//select[@name='documentType']")).select_by_visible_text("CONSULTS")

        Select(driver.find_element(By.XPATH, "//select[@name='provider']")).select_by_visible_text("KLICKOVICH MD, ROBERT")

        driver.find_element(By.XPATH, "//textarea[@name='notes']").send_keys(notes)

        # 4. Click Upload
        driver.find_element(By.XPATH, "//button[normalize-space()='Upload']").click()

        print(f"✅ Uploaded: {os.path.basename(file_path)}")

    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        raise
