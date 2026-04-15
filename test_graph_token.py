"""
Step 1 of 2 — Test Microsoft Graph token acquisition.

Verifies that MSAL can authenticate using the PFX certificate and return
an access token.  Run this before test_graph_mailbox.py.

Usage (from the project directory):
    python test_graph_token.py
"""

import os
import sys
import msal
from dotenv import load_dotenv

load_dotenv()

tenant_id    = os.getenv("GRAPH_TENANT_ID", "")
client_id    = os.getenv("GRAPH_CLIENT_ID", "")
pfx_path     = os.getenv("GRAPH_PFX_PATH", "")
pfx_password = os.getenv("GRAPH_PFX_PASSWORD", "")

missing = [k for k, v in {
    "GRAPH_TENANT_ID":    tenant_id,
    "GRAPH_CLIENT_ID":    client_id,
    "GRAPH_PFX_PATH":     pfx_path,
    "GRAPH_PFX_PASSWORD": pfx_password,
}.items() if not v]

if missing:
    print(f"ERROR: Missing values in .env: {', '.join(missing)}")
    sys.exit(1)

if not os.path.exists(pfx_path):
    print(f"ERROR: PFX file not found at: {pfx_path}")
    sys.exit(1)

print(f"Tenant ID : {tenant_id}")
print(f"Client ID : {client_id}")
print(f"PFX path  : {pfx_path}")
print(f"PFX exists: yes")
print()
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

if "access_token" in result:
    token_preview = result["access_token"][:50]
    print(f"SUCCESS — token acquired (first 50 chars): {token_preview}...")
else:
    print("FAILED — could not acquire token.")
    print(f"  error            : {result.get('error')}")
    print(f"  error_description: {result.get('error_description')}")
    sys.exit(1)
