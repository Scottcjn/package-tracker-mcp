# SPDX-License-Identifier: MIT
"""
Carrier detection and canonical tracking URLs — pure logic, no network, no keys.

A shipping tracking number encodes its carrier in its format: UPS numbers start
"1Z", Amazon Logistics start "TBA", USPS international uses the S10 letter
format, FedEx Express is a bare 12 digits, and so on. This module identifies the
carrier from that format and builds the carrier's official tracking URL with the
number pre-filled — the authoritative place to see live status.

No API keys, no scraping, no network calls. Deterministic and offline.
"""

import re

# carrier_key -> (display name, tracking-URL template)
CARRIERS = {
    "ups":    ("UPS",              "https://www.ups.com/track?tracknum={}"),
    "fedex":  ("FedEx",            "https://www.fedex.com/fedextrack/?trknbr={}"),
    "usps":   ("USPS",             "https://tools.usps.com/go/TrackConfirmAction?tLabels={}"),
    "dhl":    ("DHL",              "https://www.dhl.com/en/express/tracking.html?AWB={}"),
    "amazon": ("Amazon Logistics", "https://track.amazon.com/tracking/{}"),
    "ontrac": ("OnTrac",           "https://www.ontrac.com/tracking/?number={}"),
}

# (regex, carrier_key, confidence) — checked in order, most specific first.
# A number may match more than one carrier; all matches are returned, ranked.
_PATTERNS = [
    (r"1Z[0-9A-Z]{16}",                    "ups",    "high"),    # UPS standard
    (r"TBA[0-9]{12}",                      "amazon", "high"),    # Amazon Logistics
    (r"[CD][0-9]{14}",                     "ontrac", "high"),    # OnTrac
    (r"[A-Z]{2}[0-9]{9}[A-Z]{2}",          "usps",   "high"),    # USPS S10 international
    (r"(?:94|93|92|95|91|90)[0-9]{18,20}", "usps",   "high"),    # USPS IMpb 20-22 digit
    (r"[0-9]{12}",                         "fedex",  "high"),    # FedEx Express
    (r"[0-9]{15}",                         "fedex",  "medium"),  # FedEx Ground
    (r"(?:96|61)[0-9]{18}",                "fedex",  "medium"),  # FedEx 96-prefixed
    (r"[0-9]{10}",                         "dhl",    "medium"),  # DHL Express
    (r"[0-9]{20,22}",                      "usps",   "low"),     # generic long IMpb
]
_RANK = {"high": 0, "medium": 1, "low": 2}


def normalize(tracking_number):
    """Strip spaces and dashes, uppercase."""
    return re.sub(r"[\s\-]", "", tracking_number or "").upper()


def detect(tracking_number):
    """Identify carrier candidates for a tracking number.

    Returns a list of {carrier, name, confidence}, best confidence first.
    Empty list if no known carrier format matches.
    """
    tn = normalize(tracking_number)
    seen, out = set(), []
    for pattern, key, confidence in _PATTERNS:
        if key in seen:
            continue
        if re.fullmatch(pattern, tn):
            seen.add(key)
            out.append({"carrier": key, "name": CARRIERS[key][0],
                        "confidence": confidence})
    out.sort(key=lambda c: _RANK[c["confidence"]])
    return out


def tracking_url(carrier, tracking_number):
    """Build the carrier's official tracking URL with the number pre-filled."""
    if carrier not in CARRIERS:
        raise ValueError(f"unknown carrier: {carrier}")
    return CARRIERS[carrier][1].format(normalize(tracking_number))
