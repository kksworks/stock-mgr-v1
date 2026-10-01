"""crawler.py 현재가 수집 로직 단위/통합 검증."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import crawler


class TestParseHelpers(unittest.TestCase):
    def test_parse_naver_number_formats(self):
        self.assertEqual(crawler._parse_naver_number("6,649.28"), 6649.28)
        self.assertEqual(crawler._parse_naver_number("-35.09"), -35.09)
        self.assertEqual(crawler._parse_naver_number("0.53%"), 0.53)
        self.assertEqual(crawler._parse_naver_number(26186.41), 26186.41)
        self.assertEqual(crawler._parse_naver_number(100), 100.0)
        self.assertIsNone(crawler._parse_naver_number(None))
        self.assertIsNone(crawler._parse_naver_number("-"))
        self.assertIsNone(crawler._parse_naver_number("abc"))

    def test_quote_from_price_change_float(self):
        q = crawler._quote_from_price_change(6649.28, -35.09, -0.52)
        self.assertEqual(q["price"], 6649.28)
        self.assertEqual(q["prev_day_change"], -35.09)
        self.assertEqual(q["prev_day_change_pct"], -0.52)

    def test_quote_from_price_change_as_int(self):
        q = crawler._quote_from_price_change(249000.4, 1500.6, 0.6, as_int=True)
        self.assertEqual(q["price"], 249000)
        self.assertEqual(q["prev_day_change"], 1501)
        self.assertIsInstance(q["price"], int)
        self.assertIsInstance(q["prev_day_change"], int)

    def test_quote_from_price_change_invalid(self):
        self.assertEqual(crawler._quote_from_price_change(None, 1, 1), crawler._empty_quote())
        self.assertEqual(crawler._quote_from_price_change(0, 1, 1), crawler._empty_quote())
        self.assertEqual(crawler._quote_from_price_change(-1, 1, 1), crawler._empty_quote())

    def test_quote_from_naver_basic_payload(self):
        q = crawler._quote_from_naver_basic_payload(
            {
                "closePrice": "6,649.28",
                "compareToPreviousClosePrice": "-35.09",
                "fluctuationsRatio": "-0.52",
            }
        )
        self.assertAlmostEqual(q["price"], 6649.28)
        self.assertAlmostEqual(q["prev_day_change"], -35.09)
        self.assertAlmostEqual(q["prev_day_change_pct"], -0.52)

    def test_quote_from_naver_basic_payload_prefers_raw(self):
        q = crawler._quote_from_naver_basic_payload(
            {
                "closePrice": "26,186.41",
                "closePriceRaw": 26186.41,
                "compareToPreviousClosePrice": "-146.62",
                "compareToPreviousClosePriceRaw": -146.62,
                "fluctuationsRatio": "-0.56",
                "fluctuationsRatioRaw": -0.56,
            }
        )
        self.assertEqual(q["price"], 26186.41)
        self.assertEqual(q["prev_day_change"], -146.62)
        self.assertEqual(q["prev_day_change_pct"], -0.56)

    def test_naver_api_headers(self):
        h = crawler._naver_api_headers("https://stock.naver.com/x", origin="https://stock.naver.com")
        self.assertEqual(h["Referer"], "https://stock.naver.com/x")
        self.assertEqual(h["Origin"], "https://stock.naver.com")
        self.assertIn("Mozilla", h["User-Agent"])
        h2 = crawler._naver_api_headers("https://stock.naver.com/y")
        self.assertNotIn("Origin", h2)


class TestFetchWithMocks(unittest.TestCase):
    def test_fetch_index_price_kospi(self):
        payload = {
            "closePrice": "6,649.28",
            "compareToPreviousClosePrice": "-35.09",
            "fluctuationsRatio": "-0.52",
        }
        with patch.object(crawler, "_naver_get_json", return_value=payload) as mock_get:
            q = crawler.fetch_index_price("KOSPI")
        self.assertGreater(q["price"], 0)
        self.assertAlmostEqual(q["prev_day_change"], -35.09)
        self.assertAlmostEqual(q["prev_day_change_pct"], -0.52)
        url = mock_get.call_args[0][0]
        self.assertIn("/api/securityFe/api/index/KOSPI/basic", url)

    def test_fetch_domestic_stock_quote_from_minute5(self):
        payload = {
            "priceInfos": [
                {"currentPrice": 248500.0},
                {"currentPrice": 249500.0},
            ],
            "lastClosePrice": 249000.0,
        }
        with patch.object(crawler, "_naver_get_json", return_value=payload) as mock_get:
            q = crawler.fetch_domestic_stock_quote("005930")
        self.assertEqual(q["price"], 249500)
        self.assertEqual(q["prev_day_change"], 500)
        self.assertAlmostEqual(q["prev_day_change_pct"], 500 / 249000 * 100)
        url = mock_get.call_args[0][0]
        self.assertIn("/chart/domestic/item/005930/minute5", url)
        headers = mock_get.call_args[0][1]
        self.assertEqual(headers.get("Origin"), "https://stock.naver.com")

    def test_fetch_domestic_stock_quote_empty_infos(self):
        with patch.object(crawler, "_naver_get_json", return_value={"priceInfos": [], "lastClosePrice": 1}):
            q = crawler.fetch_domestic_stock_quote("005930")
        self.assertEqual(q, crawler._empty_quote())

    def test_fetch_world_sise_quote(self):
        payload = {
            "closePriceRaw": 26186.41,
            "compareToPreviousClosePriceRaw": -146.62,
            "fluctuationsRatioRaw": -0.56,
        }
        with patch.object(crawler, "_naver_get_json", return_value=payload) as mock_get:
            q = crawler.fetch_world_sise_quote(".IXIC")
        self.assertEqual(q["price"], 26186.41)
        self.assertEqual(q["prev_day_change"], -146.62)
        self.assertIn("/index/.IXIC/basic", mock_get.call_args[0][0])

    def test_fetch_exchange_detail_quote(self):
        payload = {
            "exchangeInfo": {
                "calcPrice": 1346.0,
                "closePrice": "1,346.00",
                "fluctuations": -2.5,
                "fluctuationsRatio": -0.19,
            }
        }
        with patch.object(crawler, "_naver_get_json", return_value=payload) as mock_get:
            q = crawler.fetch_exchange_detail_quote("FX_USDKRW")
        self.assertEqual(q["price"], 1346.0)
        self.assertEqual(q["prev_day_change"], -2.5)
        self.assertEqual(q["prev_day_change_pct"], -0.19)
        self.assertIn("/marketindex/exchange/FX_USDKRW", mock_get.call_args[0][0])

    def test_fetch_stock_quote_routing(self):
        with patch.object(crawler, "fetch_exchange_detail_quote", return_value={"price": 1}) as fx:
            self.assertEqual(crawler.fetch_stock_quote("USDKRW")["price"], 1)
            fx.assert_called_once_with("FX_USDKRW")

        with patch.object(crawler, "fetch_world_sise_quote", return_value={"price": 2}) as world:
            self.assertEqual(crawler.fetch_stock_quote("NASDAQ")["price"], 2)
            world.assert_called_once_with(".IXIC")
            self.assertEqual(crawler.fetch_stock_quote("SP500")["price"], 2)
            world.assert_called_with(".INX")

        with patch.object(crawler, "fetch_index_price", return_value={"price": 3}) as idx:
            self.assertEqual(crawler.fetch_stock_quote("KOSPI")["price"], 3)
            idx.assert_called_once_with("KOSPI")

        with patch.object(crawler, "fetch_domestic_stock_quote", return_value={"price": 4}) as stock:
            self.assertEqual(crawler.fetch_stock_quote("005930")["price"], 4)
            stock.assert_called_once_with("005930")

    def test_fetch_stock_price_compat(self):
        with patch.object(crawler, "fetch_stock_quote", return_value={"price": 249000}):
            self.assertEqual(crawler.fetch_stock_price("005930"), 249000)

    def test_fetch_index_price_on_exception_returns_empty(self):
        with patch.object(crawler, "_naver_get_json", side_effect=RuntimeError("boom")):
            q = crawler.fetch_index_price("KOSPI")
        self.assertEqual(q, crawler._empty_quote())


@unittest.skipUnless(
    os.environ.get("CRAWLER_LIVE_TEST", "1") == "1",
    "set CRAWLER_LIVE_TEST=1 to enable live API checks",
)
class TestLiveNaverApis(unittest.TestCase):
    """실제 Naver API 호출 스모크 테스트 (기본 활성)."""

    def _assert_valid_quote(self, q, *, expect_int_price=False):
        self.assertIsInstance(q, dict)
        self.assertIn("price", q)
        self.assertIn("prev_day_change", q)
        self.assertIn("prev_day_change_pct", q)
        self.assertGreater(q["price"], 0)
        self.assertIsNotNone(q["prev_day_change"])
        self.assertIsNotNone(q["prev_day_change_pct"])
        if expect_int_price:
            self.assertIsInstance(q["price"], int)

    def test_live_kospi(self):
        self._assert_valid_quote(crawler.fetch_index_price("KOSPI"))

    def test_live_kosdaq(self):
        self._assert_valid_quote(crawler.fetch_index_price("KOSDAQ"))

    def test_live_samsung(self):
        self._assert_valid_quote(crawler.fetch_domestic_stock_quote("005930"), expect_int_price=True)

    def test_live_nasdaq(self):
        self._assert_valid_quote(crawler.fetch_stock_quote("NASDAQ"))

    def test_live_sp500(self):
        self._assert_valid_quote(crawler.fetch_stock_quote("SP500"))

    def test_live_usdkrw(self):
        self._assert_valid_quote(crawler.fetch_stock_quote("USDKRW"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
