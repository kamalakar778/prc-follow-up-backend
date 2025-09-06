# Import the PRC_FOLDER and file_name_storage from main.py
from main import PRC_FOLDER, file_name_storage

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Extract the file names from file_name_storage (assuming it's a dictionary)
file1_name = file_name_storage.get("last_uploaded")  # Get the last uploaded file name
file2_name = file_name_storage.get("last_uploaded")  # If both files are same, we can use the same for file2

# Check if file names are found
if not file1_name or not file2_name:
    print("Error: 'file1' or 'file2' names could not be retrieved from file_name_storage.")
    exit()

print(f"Extracted file names: file1 = {file1_name}, file2 = {file2_name}")

# Define the paths dynamically based on PRC_FOLDER from main.py
path1 = os.path.join(PRC_FOLDER, file1_name)  # Path 1 for file1
path2 = os.path.join(PRC_FOLDER, "PDF", file2_name)  # Path 2 for file2 (PDF subfolder)

# Setup WebDriver (Chrome in this case)
driver = webdriver.Chrome()  # Make sure chromedriver is installed and on PATH
wait = WebDriverWait(driver, 20)

# Step 1: Open the URL
driver.get("https://txn2.healthfusionclaims.com/electronic/pm/patient_doc.jsp")

# Step 2: Click on text = "Upload Document"
upload_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Upload Document")))
upload_button.click()

# Function to handle file upload
def upload_file(file_path, file_name):
    # Step 3: Fill first input with Document Title
    input_boxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='text']")))

    # Clear and fill the first input box with the file name
    input_boxes[0].clear()
    input_boxes[0].send_keys(file_name)

    # Step 4: Click on Choose File and upload the document
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(file_path)

    # Step 5: Choose "consults" from dropdown under "Document Type"
    doc_type_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@name, 'docType')]")))

    # Select "consults" option
    Select(doc_type_dropdown).select_by_visible_text("consults")

    # Step 6: Choose "KLICKOVICH MD, ROBERT" from Provider dropdown
    provider_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@name, 'provider')]")))

    # Select the provider "KLICKOVICH MD, ROBERT"
    Select(provider_dropdown).select_by_visible_text("KLICKOVICH MD, ROBERT")

    # Step 7: Re-enter Document Title in the second input field
    title_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
    if len(title_inputs) >= 2:
        title_inputs[1].clear()
        title_inputs[1].send_keys(file_name)

    # Step 8: Click the "Upload" button
    upload_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Upload')]")
    upload_btn.click()

# Upload first file using path1
upload_file(path1, file1_name)

# Step 9: Wait for upload to complete and then upload second file using path2
time.sleep(10)  # Adjust time as needed for the upload to complete
upload_file(path2, file2_name)

# Optional: Close browser after done
time.sleep(5)
driver.quit()

