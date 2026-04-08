# [1.0.0](https://github.com/Paul-Transportation/Transporeon_Bidding_Bot/releases/tag/v1.0.0) (2024-01-01)

## Features

* XPath-based DOM scraping of the Transporeon load board (`#PublishedTransportListViewCarrierGrid`)
* All-in bid submission via browser automation (single price covering transport + fuel)
* DAT spot market pricing (`perTrip.rateUsd` + `averageFuelSurchargePerTripUsd`) as base rate
* Configurable bidding rules via `pli_bidding_rules` (lane, shipper, equipment, lead time, accessorials)
* Flask control API on port 8001 (on/off toggle, dry-run mode, schedule control, rule reload)
* Prometheus metrics endpoint on port 8000
* Browser session restart every 2 hours to prevent Transporeon session timeouts
* PIA VPN IP rotation to avoid rate limiting
* Email alerts for bid notifications and login failures
* Bid history logging to `pli_bidding` table on AVRLDS01
