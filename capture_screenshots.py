import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1280,1100")

driver = webdriver.Chrome(options=options)

questions = [
    ("q1_privilege_leave.png", "How many days of Privilege Leave (PL) does a permanent employee get per year?"),
    ("q2_probation_period.png", "What is the probation period for employees up to Senior Manager?"),
    ("q3_health_insurance.png", "What is the company's health-insurance premium amount?"),
    ("q4_gst_rate.png", "What is the current GST rate in India?"),
    ("q5_maternity_leave.png", "How many days of maternity leave are given?"),
]

try:
    for filename, q_text in questions:
        print(f"Capturing: {filename} for query: '{q_text}'...")
        driver.get("http://localhost:8501")
        time.sleep(3)

        # Find the text input box
        inputs = driver.find_elements(By.TAG_NAME, "input")
        target_input = None
        for inp in inputs:
            if inp.get_attribute("type") == "text":
                target_input = inp
                break

        if target_input:
            target_input.click()
            # Clear input
            target_input.send_keys(Keys.COMMAND + "a")
            target_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            target_input.send_keys(q_text)
            time.sleep(0.5)

            # Click the search button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            search_btn = None
            for b in buttons:
                if "Search HR Policy" in b.text:
                    search_btn = b
                    break

            if search_btn:
                search_btn.click()
            else:
                target_input.send_keys(Keys.RETURN)

            time.sleep(7)
            save_path = f"screenshots/{filename}"
            driver.save_screenshot(save_path)
            print(f"Saved: {save_path}")

finally:
    driver.quit()
    print("All screenshots successfully captured!")
