"""Tests for carrier detection — pure logic, no network. Run: python3 test_carriers.py"""

import sys

from carriers import detect, normalize, tracking_url


def test_normalize():
    assert normalize(" 1z 999-aa1 ") == "1Z999AA1"
    assert normalize("381450145381") == "381450145381"


def test_fedex_12_digit():
    c = detect("123456789012")          # a bare 12-digit FedEx Express number
    assert c and c[0]["carrier"] == "fedex" and c[0]["confidence"] == "high"


def test_ups_1z():
    c = detect("1Z999AA10123456784")
    assert c and c[0]["carrier"] == "ups"


def test_amazon_tba():
    c = detect("TBA303939011234")
    assert c and c[0]["carrier"] == "amazon"


def test_usps_international():
    c = detect("EA123456789US")
    assert c and c[0]["carrier"] == "usps"


def test_usps_impb():
    c = detect("9400111899223817612345")
    assert any(x["carrier"] == "usps" for x in c)


def test_dashes_and_spaces_ignored():
    c = detect("1Z 999-AA1-0123-456784")
    assert c and c[0]["carrier"] == "ups"


def test_unknown_returns_empty():
    assert detect("hello world") == []


def test_tracking_url():
    url = tracking_url("fedex", "123456789012")
    assert "123456789012" in url and "fedex.com" in url


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
