from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Utilities.utils import web_driver_wait_by_xpath
import time
from Utilities.countdown import countdown


def login(driver, user, password, website, totp_secret=None):
    """
    This function will log in with the given url and user account info
        driver: driver from selenium to use
        account: Account ot log in with
        user: user name for the loadboard
        password: password for the loadboard
        website: the website to log in to
        totp_secret: optional base32 TOTP secret (from config.json totp_secret field);
                     if empty or None, 2FA handling is skipped entirely
    """
    driver.get(website)
    time.sleep(10)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_email-input']").send_keys(user)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_password-input']").send_keys(password)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_submit']/div").click()
    countdown(3)

    # --- TOTP 2FA handling ---
    # Only runs if a totp_secret is configured. Tries to detect a 2FA input field
    # on the page after login. If no prompt appears, this block exits silently and
    # the normal login flow continues unchanged.
    if totp_secret:
        try:
            import pyotp
            totp_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, (
                    "input[autocomplete='one-time-code'],"
                    "input[name*='otp'],"
                    "input[id*='otp'],"
                    "input[name*='totp'],"
                    "input[id*='totp'],"
                    "input[name*='code'],"
                    "input[id*='code']"
                )))
            )
            totp_field.send_keys(pyotp.TOTP(totp_secret).now())
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception:
                totp_field.send_keys(Keys.RETURN)
            countdown(3)
        except Exception:
            # No 2FA prompt found — continue with normal login flow
            pass
    # --- End TOTP handling ---

    driver.maximize_window()
    countdown(10)
