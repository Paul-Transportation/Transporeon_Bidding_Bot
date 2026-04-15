"""Microsoft Graph API helper — retrieves a Transporeon 2FA code from email.

Authentication uses app-only (client credentials) flow with a PFX certificate.
The PFX file must be stored outside the project directory and must never be
committed to source control.
"""

import msal
import requests
import re
import time
from datetime import datetime, timezone, timedelta


def get_2fa_code_from_email(
    tenant_id,
    client_id,
    pfx_path,
    pfx_password,
    mailbox,
    received_after=None,
    max_wait_seconds=60,
    poll_interval=5,
    sender_filter="transporeon",
):
    """
    Acquires a Microsoft Graph token via certificate-based client credentials,
    then polls the given mailbox for a recent email from Transporeon that
    contains a 6-digit 2FA code.

    Parameters
    ----------
    tenant_id        : Azure AD tenant ID
    client_id        : App registration client ID
    pfx_path         : Absolute path to the .pfx certificate file on disk
    pfx_password     : Passphrase for the .pfx file (None if unprotected)
    mailbox          : UPN of the mailbox to read (e.g. "Trenton.Sims@paulinc.com")
    received_after   : Timezone-aware UTC datetime; only emails received after
                       this point are considered, preventing stale codes from a
                       previous session.  Defaults to 2 minutes ago if omitted.
    max_wait_seconds : How long to keep polling before giving up (default 60 s)
    poll_interval    : Seconds between Graph API calls (default 5 s)
    sender_filter    : Case-insensitive substring matched against the sender address

    Returns
    -------
    str — the extracted 6-digit code

    Raises
    ------
    RuntimeError  if the Graph token cannot be acquired
    TimeoutError  if no matching email arrives within max_wait_seconds
    """
    if received_after is None:
        received_after = datetime.now(timezone.utc) - timedelta(minutes=2)

    # --- Authenticate with certificate ---
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential={
            "private_key_pfx_path": pfx_path,
            "passphrase": pfx_password,
        },
    )
    token_result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in token_result:
        raise RuntimeError(
            f"Graph token acquisition failed: "
            f"{token_result.get('error_description', token_result)}"
        )

    headers = {"Authorization": f"Bearer {token_result['access_token']}"}
    received_after_str = received_after.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages"
    params = {
        "$filter": f"receivedDateTime gt {received_after_str}",
        "$orderby": "receivedDateTime desc",
        "$top": 10,
        "$select": "subject,body,receivedDateTime,from",
    }

    # --- Poll for the code ---
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()

        for msg in resp.json().get("value", []):
            from_addr = (
                msg.get("from", {})
                   .get("emailAddress", {})
                   .get("address", "")
                   .lower()
            )
            if sender_filter.lower() not in from_addr:
                continue

            body = msg.get("body", {}).get("content", "")
            match = re.search(r'\b(\d{6})\b', body)
            if match:
                return match.group(1)

        time.sleep(poll_interval)

    raise TimeoutError(
        f"No 2FA code email from '{sender_filter}' arrived in {mailbox} "
        f"within {max_wait_seconds} s"
    )
