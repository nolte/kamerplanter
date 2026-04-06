from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

options = webdriver.ChromeOptions()
driver = webdriver.Remote(
    command_executor='http://selenium-hub:4444/wd/hub',
    options=options
)

try:
    driver.get('http://frontend:80/pflanzenschutz/pests')
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='pest-list-page']")))
    time.sleep(1)

    btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='create-button']")))
    btn.click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='dialog']")))
    time.sleep(0.5)

    driver.execute_script("""
        window.__submitFired = false;
        window.__clickFired = false;
        document.addEventListener('submit', function(e) {
            window.__submitFired = true;
        }, true);
        document.addEventListener('click', function(e) {
            var testid = e.target && e.target.getAttribute && e.target.getAttribute('data-testid');
            if (testid === 'form-submit-button') {
                window.__clickFired = true;
            }
        }, true);
    """)

    submit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='form-submit-button']")))
    driver.execute_script('arguments[0].scrollIntoView({block: "center"});', submit_btn)

    print('Button tag:', submit_btn.tag_name)
    print('Button type:', submit_btn.get_attribute('type'))
    print('Button disabled:', submit_btn.get_attribute('disabled'))
    print('Button visible:', submit_btn.is_displayed())
    print('Button enabled:', submit_btn.is_enabled())

    is_in_form = driver.execute_script("return !!arguments[0].form;", submit_btn)
    print('Button has .form:', is_in_form)

    ActionChains(driver).move_to_element(submit_btn).click().perform()
    time.sleep(1)

    submit_fired = driver.execute_script('return window.__submitFired;')
    click_fired = driver.execute_script('return window.__clickFired;')
    print('Submit event fired:', submit_fired)
    print('Click on submit btn fired:', click_fired)

    sci = driver.find_element(By.CSS_SELECTOR, "[data-testid='form-field-scientific_name'] input")
    print('scientific_name aria-invalid after submit:', sci.get_attribute('aria-invalid'))
    errors = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] .Mui-error")
    print('Mui-error elements:', len(errors))

    # Now try dispatching submit event directly on the form
    print('\n--- Dispatching submit event directly on form ---')
    driver.execute_script("""
        window.__submitFired2 = false;
        document.addEventListener('submit', function(e) { window.__submitFired2 = true; }, true);
        var form = document.querySelector("div[role='dialog'] form");
        if (form) {
            var ev = new Event('submit', {bubbles: true, cancelable: true});
            form.dispatchEvent(ev);
        }
    """)
    time.sleep(1)
    print('Submit fired via dispatchEvent:', driver.execute_script('return window.__submitFired2;'))
    sci2 = driver.find_element(By.CSS_SELECTOR, "[data-testid='form-field-scientific_name'] input")
    print('scientific_name aria-invalid after dispatchEvent:', sci2.get_attribute('aria-invalid'))

finally:
    driver.quit()
