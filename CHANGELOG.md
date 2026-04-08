# [1.1.0](https://github.com/Paul-Transportation/Transporeon_Bidding_Bot/compare/v1.0.0...v1.1.0) (2026-04-08)

### Bug Fixes

* prevent bid submission crash when placeOffer dialog fails to open ([8ac6590](https://github.com/Paul-Transportation/Transporeon_Bidding_Bot/commit/8ac6590b39b798bcaf350f4f678b1202678b3e5e))
* increase modal render wait time from 1s to 2s to allow dialog to fully load ([8ac6590](https://github.com/Paul-Transportation/Transporeon_Bidding_Bot/commit/8ac6590b39b798bcaf350f4f678b1202678b3e5e))

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
