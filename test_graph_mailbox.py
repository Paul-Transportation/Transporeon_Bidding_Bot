"""
Step 2 of 2 — Test Microsoft Graph mailbox read.

Confirms that the app can read recent messages from the configured mailbox.
Run test_graph_token.py first to verify token acquisition before this.

Usage (from the project directory):
    python test_graph_mailbox.py
"""

import os
import sys
import msal
import requests
from dotenv import load_dotenv

load_dotenv()

tenant_id    = os.getenv("GRAPH_TENANT_ID", "")
client_id    = os.getenv("GRAPH_CLIENT_ID", "")
pfx_path     = os.getenv("GRAPH_PFX_PATH", "")
pfx_password = os.getenv("GRAPH_PFX_PASSWORD", "")
mailbox      = os.getenv("GRAPH_MAILBOX", "Trenton.Sims@paulinc.com")

missing = [k for k, v in {
    "GRAPH_TENANT_ID":    tenant_id,
    "GRAPH_CLIENT_ID":    client_id,
    "GRAPH_PFX_PATH":     pfx_path,
    "GRAPH_PFX_PASSWORD": pfx_password,
}.items() if not v]

if missing:
    print(f"ERROR: Missing values in .env: {', '.join(missing)}")
    sys.exit(1)

# --- Acquire token ---
print(f"Mailbox   : {mailbox}")
print("Requesting token...")

app = msal.ConfidentialClientApplication(
    client_id=client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential={
        "private_key_pfx_path": pfx_path,
        "passphrase": pfx_password,
    },
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

if "access_token" not in result:
    print("FAILED — could not acquire token.")
    print(f"  error            : {result.get('error')}")
    print(f"  error_description: {result.get('error_description')}")
    sys.exit(1)

print("Token acquired.")
print()

# --- Read mailbox ---
print(f"Reading 5 most recent messages from {mailbox}...")
print()

headers = {"Authorization": f"Bearer {result['access_token']}"}
resp = requests.get(
    f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages",
    headers=headers,
    params={
        "$top": "5",
        "$select": "subject,receivedDateTime,from",
        "$orderby": "receivedDateTime desc",
    },
)

if not resp.ok:
    print(f"FAILED — Graph API returned {resp.status_code}:")
    print(resp.text)
    sys.exit(1)

messages = resp.json().get("value", [])

if not messages:
    print("No messages found (mailbox may be empty or permissions are too narrow).")
else:
    print(f"{'Received':<30} {'From':<40} Subject")
    print("-" * 100)
    for msg in messages:
        received = msg.get("receivedDateTime", "")
        from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "")
        subject = msg.get("subject", "")
        print(f"{received:<30} {from_addr:<40} {subject}")

print()
print("SUCCESS — mailbox is readable.")
