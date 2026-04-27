# Transporeon Bidding Bot

Automated spot bidding bot for the **Transporeon** load board. Monitors available freight, evaluates each load against configurable business rules, prices using DAT market rates, and submits bids via browser automation.

- **Server:** LG09 (AWS WorkSpace, Windows)
- **Location:** `C:\Bots\Transporeon_Bidding_Bot`
- **Platform:** Transporeon (transporeon.com)
- **Bid type:** All-in (single price including transport + fuel)
- **Database:** `bidding` on **AVRLDS01:3306** (MariaDB 11.3, MySQL-protocol compatible), user `bidding_user`
- **Rules managed via:** Centralized **Bidding Rules Editor** at **`http://AVRLDS01:8002`** (canonical instance — Flask, bare `python rules_backend.py`)
- **Run model:** Manually launched via `.\deploy_script.ps1` after each deploy — **no Windows service, no Task Scheduler entry, no PM2** (Apr 2026 audit)
- **2FA:** Email-based; codes read from Outlook via Microsoft Graph using certificate auth (see [Microsoft Graph 2FA](#microsoft-graph-2fa))
- **Developer guide:** [knowledge-base/bot-guides/transporeon-bot.md](https://github.com/Paul-Transportation/paul-dev-docs/blob/main/knowledge-base/bot-guides/transporeon-bot.md)

---

## Quick Start

```powershell
# Activate virtual environment and start the bot
.\deploy_script.ps1

# Or manually:
.\myvenv\Scripts\activate
python main.py
```

---

## Project Structure

```text
main.py                  # Entry point: login loop + bot restart loop
login.py                 # Selenium login to Transporeon
_bot.py                  # Main bot loop: refresh → scrape → evaluate → bid
check_restriction.py     # Business rules engine
server.py                # Flask control API (port 8001)
config.json              # Runtime config (on/off, bidding, schedule, prometheus_port)
deploy_script.ps1        # Activation + launch script
requirements.txt         # Python dependencies
Utilities/
  __init__.py            # Initializes Storage, Prometheus, loads config
  Storage.py             # DB connection + CRUD (rules, DSM list, bid log)
  bot_functions.py       # Core helpers: scrape loads, submit bids, refresh
  make_dat_call.py       # DAT API integration (market rate lookups)
  call_eia.py            # EIA API (diesel price for fuel surcharge)
  email.py               # SMTP error/notification emails
  logger_config.py       # Rotating file loggers (Info + Errors)
  countdown.py           # Visual countdown timer
  utils.py               # Selenium helpers, date utils, screenshot saving
  pia.py                 # PIA VPN region switching
  db.py                  # Legacy DB helper + Prometheus server start
  fuel_table.json        # Diesel price → $/mile surcharge lookup table
```

---

## Configuration

`config.json` controls runtime behavior:

```json
{
  "on": 1,
  "bidding": 0,
  "schedule": {
    "enabled": true,
    "timezone": "America/Chicago",
    "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "start": "07:00",
    "end": "18:00"
  },
  "prometheus_port": 8000
}
```

| Key | Description |
| --- | ----------- |
| `on` | `1` = bot active, `0` = paused (no loads processed) |
| `bidding` | `1` = submit real bids, `0` = dry-run (evaluate only, no submissions) |
| `schedule` | Time window enforcement; bot sleeps outside configured hours |
| `prometheus_port` | Port for Prometheus metrics (default `8000`) |

---

## Ports

| Port | Purpose |
| ---- | ------- |
| `8000` | Prometheus metrics |
| `8001` | Flask bot control API |

---

## Bot Control API (port 8001)

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/toggle-on` | Toggle bot on/off |
| `GET` | `/toggle-bidding` | Toggle bidding mode on/off |
| `GET` | `/status` | Return current `on` and `bidding` state |
| `GET` | `/reload-rules` | Hot-reload rules/variables/shippers from DB |
| `GET` | `/schedule` | Return current schedule config |
| `PUT` | `/schedule` | Update schedule (days, start, end, timezone) |
| `GET` | `/prometheus-port` | Return configured Prometheus port |
| `PUT` | `/prometheus-port/<port>` | Update Prometheus port |

---

## How It Works

1. **Login** — Selenium Wire opens Edge and authenticates to `transporeon.com` using credentials stored in `AVRLDS01.bidding.pli_loadboard_accounts`.
2. **Refresh** — Every ~2 minutes, the page is refreshed and the load table is scraped via XPath.
3. **Scrape** — Each row in `PublishedTransportListViewCarrierGrid` yields a load dict (origin, destination, shipper, equipment, weight, dates, etc.).
4. **DSM check** — Loads seen in the last 7 days (via `pli_bidding`) are skipped.
5. **DAT rate lookup** — Calls `https://analytics.api.dat.com/linehaulrates/v1/lookups` for current market rates; auto-refreshes expired tokens.
6. **Rules engine** — `check_lane_restrictions()` in `check_restriction.py` evaluates every active rule from the DB. Rules can ADD/SUBTRACT/SET amounts, apply per-stop premiums, or reject the load outright (`no_bid`).
7. **Bid** — If approved and `bidding=1`: clicks "Place Offer" button, enters the calculated amount, and confirms. If `bidding=0`: sends a notification email only.
8. **Log** — Every processed load (bid or reject) is inserted into `pli_bidding`.
9. **Restart** — Browser session restarts every 2 hours (even-hour boundary) to avoid memory leaks and session timeouts.

---

## Email Notifications

Sent via SMTP (`paulinc-com.mail.eo.outlook.com:25`):

| Event | Recipients |
| ----- | ---------- |
| Load bid placed / dry-run notification | `it-dev@paulinc.com`, `Mackayla.Dooley@paulinc.com` |
| Bid submission error | `it-dev@paulinc.com` |
| Login failure (after 3 retries) | `becca.romas@paulinc.com`, `Trenton.Sims@paulinc.com` |

---

## Logs

| Type | Location |
| ---- | -------- |
| Info | `.\Logs\Info\` — daily rotation |
| Errors | `.\Logs\Errors\` — daily rotation |
| Screenshots | `.\Logs\Screenshots\` — on bid submission errors |
| Page sources | `.\Logs\Page_Sources\` — HTML snapshots for DOM debugging |

---

## Restart Procedure

```powershell
# RDP to LG09, then in PowerShell from C:\Bots\Transporeon_Bidding_Bot:
.\deploy_script.ps1

# If browser processes are stuck:
Get-Process msedge, msedgedriver | Stop-Process -Force
```

---

## Rules Management

Rules, variables, and shipper settings are managed via the **centralized Bidding Rules Editor** at **`http://AVRLDS01:8002`** (Flask, bare `python rules_backend.py`, install path `C:\Users\Trenton.Sims\Desktop\BiddingRulesEditor` on AVRLDS01). After saving rules, the bot picks them up automatically via `GET /reload-rules` on its control API.

See the [BiddingRulesEditor repo](../BiddingRulesEditor) for details. Per-bot copies of `rules_backend.py` inside this repo need reconciliation against the canonical deployment.

---

## Microsoft Graph 2FA

Transporeon's login flow requires an email-based 2FA code on every session. The bot retrieves codes from Outlook automatically using the **Microsoft Graph API** with **certificate authentication** (no shared mailbox password):

| Item | Value |
| --- | --- |
| Auth flow | Azure AD app registration → client-credentials grant via `.pfx` certificate |
| Cert path on LG09 | `C:\Secure\PaulGraphMailReader.pfx` (filename as deployed 2026-04-16) |
| Mailbox | The mailbox the bot polls for 2FA codes |
| App registration | Display name and owner unconfirmed — tracked in `paul-dev-docs/knowledge-base/open-items.md` |

> **Cert rotation:** When the `.pfx` is rotated, update both the file at `C:\Secure\PaulGraphMailReader.pfx` and the Azure AD app registration's certificate.

---

## Dependencies

| Library | Purpose |
| ------- | ------- |
| `selenium-wire` | Browser automation + network interception |
| `flask` + `flask_cors` | Bot control API |
| `PyMySQL` / `mysql-connector` | MariaDB connection |
| `prometheus_client` | Metrics exposure |
| `requests` + `ujson` | DAT / EIA API calls |
| `pika` | RabbitMQ (imported but not actively used in this bot) |
