from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# Replace with your actual file paths
file1_path = "/absolute/path/to/file1.pdf"
file2_path = "/absolute/path/to/file2.pdf"

# Setup WebDriver (Chrome in this case)
driver = webdriver.Chrome()  # Make sure chromedriver is installed and on PATH
wait = WebDriverWait(driver, 20)

# Step 1: Open the URL
driver.get("https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp")

# Step 2: Click on text = "Upload Document"
upload_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Upload Document")))
upload_button.click()

# Step 3: Get Document Title from frontend
# If Document Title is dynamically populated from frontend like Demography.jsx, it's assumed visible in the page DOM.
# You need to inspect and get the right element. Here we assume it's in an element with id="docTitle"
document_title = wait.until(EC.visibility_of_element_located((By.ID, "docTitle"))).text

def upload_file(file_path):
    # Step 4: Fill first input with Document Title
    input_boxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='text']")))
    input_boxes[0].clear()
    input_boxes[0].send_keys(document_title)

    # Step 5: Click on Choose File
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(file_path)

    # Step 6: Choose "consults" from dropdown under "Document Type"
    doc_type_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@name, 'docType')]")))
    Select(doc_type_dropdown).select_by_visible_text("consults")

    # Step 7: Choose "KLICKOVICH MD, ROBERT" from Provider dropdown
    provider_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@name, 'provider')]")))
    Select(provider_dropdown).select_by_visible_text("KLICKOVICH MD, ROBERT")

    # Step 8: Re-enter Document Title
    title_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    if len(title_inputs) >= 2:
        title_inputs[1].clear()
        title_inputs[1].send_keys(document_title)

    # Step 9: Click Upload button
    upload_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Upload')]")
    upload_btn.click()

# Upload first file
upload_file(file1_path)

# Step 10: Wait and repeat for second file
time.sleep(10)
upload_file(file2_path)

# Optional: Close browser after done
time.sleep(5)
driver.quit()
