from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from Utilities.utils import web_driver_wait_by_xpath
from Utilities.logger_config import logger
import time
from Utilities.countdown import countdown
from datetime import datetime, timezone


def login(driver, user, password, website, graph_2fa_config=None):
    """
    Log in to Transporeon and handle email-based 2FA if a prompt appears.

        driver           : Selenium WebDriver instance
        user             : Transporeon username (email address)
        password         : Transporeon password
        website          : Load board URL
        graph_2fa_config : dict with keys tenant_id, client_id, pfx_path,
                           pfx_password, mailbox — all required when email 2FA
                           is active.  Pass None to skip 2FA handling entirely.
    """
    driver.get(website)
    time.sleep(10)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_email-input']").send_keys(user)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_password-input']").send_keys(password)
    web_driver_wait_by_xpath(driver, 5, "//*[@id='emailForm_submit']/div").click()
    countdown(3)

    # --- Email-based 2FA handling ---
    # Only runs when all graph_2fa_config keys are populated.  After clicking
    # login, waits up to 15 s for a 2FA code input to appear on the page.  If
    # one is detected, fetches the code from the Transporeon email delivered to
    # the configured mailbox via Microsoft Graph, then submits it.  If no prompt
    # appears within the detection window the block exits silently and the normal
    # login flow continues unchanged.
    _cfg = graph_2fa_config or {}
    if all(_cfg.get(k) for k in ("tenant_id", "client_id", "pfx_path", "pfx_password", "mailbox")):
        try:
            requested_at = datetime.now(timezone.utc)
            totp_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, (
                    "input[autocomplete='one-time-code'],"
                    "input[name*='otp'],"
                    "input[id*='otp'],"
                    "input[name*='code'],"
                    "input[id*='code'],"
                    "input[name*='verification'],"
                    "input[id*='verification']"
                )))
            )
            logger.info("2FA prompt detected; fetching code from Microsoft Graph...")
            from Utilities.graph_mail import get_2fa_code_from_email
            code = get_2fa_code_from_email(
                tenant_id=_cfg["tenant_id"],
                client_id=_cfg["client_id"],
                pfx_path=_cfg["pfx_path"],
                pfx_password=_cfg["pfx_password"],
                mailbox=_cfg["mailbox"],
                received_after=requested_at,
            )
            logger.info("2FA code retrieved; submitting.")
            totp_field.send_keys(code)
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception:
                totp_field.send_keys(Keys.RETURN)
            countdown(3)
        except TimeoutException:
            # No 2FA prompt appeared — continue with normal login flow
            pass
    # --- End 2FA handling ---

    driver.maximize_window()
    countdown(10)
