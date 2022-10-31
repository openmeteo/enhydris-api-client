import datetime as dt
from io import StringIO
from unittest import TestCase

import pandas as pd
import requests
from htimeseries import HTimeseries

from enhydris_api_client import EnhydrisApiClient

from . import (
    mock_session,
    test_timeseries_csv,
    test_timeseries_csv_bottom,
    test_timeseries_hts,
)


class ReadTsDataTestCase(TestCase):
    @mock_session(**{"get.return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.read_tsdata(41, 42, 43)

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/api/stations/41/timeseriesgroups/42/timeseries/43/"
            "data/",
            params={"fmt": "hts", "start_date": None, "end_date": None},
        )

    def test_returns_data(self):
        pd.testing.assert_frame_equal(self.data.data, test_timeseries_hts.data)


class ReadTsDataWithStartAndEndDateTestCase(TestCase):
    @mock_session(**{"get.return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.read_tsdata(
            41,
            42,
            43,
            start_date=dt.datetime(2019, 6, 12, 0, 0),
            end_date=dt.datetime(2019, 6, 13, 15, 25),
        )

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/api/stations/41/timeseriesgroups/42/timeseries/43/"
            "data/",
            params={
                "fmt": "hts",
                "start_date": "2019-06-12T00:00:00",
                "end_date": "2019-06-13T15:25:00",
            },
        )

    def test_returns_data(self):
        pd.testing.assert_frame_equal(self.data.data, test_timeseries_hts.data)


class ReadEmptyTsDataTestCase(TestCase):
    @mock_session(**{"get.return_value.text": ""})
    def test_returns_data(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.read_tsdata(41, 42, 43)
        pd.testing.assert_frame_equal(self.data.data, HTimeseries().data)


class ReadTsDataErrorTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            self.client.read_tsdata(41, 42, 43)


class PostTsDataTestCase(TestCase):
    @mock_session()
    def test_makes_request(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        client.post_tsdata(41, 42, 43, test_timeseries_hts)
        f = StringIO()
        test_timeseries_hts.data.to_csv(f, header=False)
        mock_requests_session.return_value.post.assert_called_once_with(
            "https://mydomain.com/api/stations/41/timeseriesgroups/42/timeseries/43/"
            "data/",
            data={"timeseries_records": f.getvalue()},
        )

    @mock_session(**{"post.return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            client.post_tsdata(41, 42, 43, test_timeseries_hts)


class GetTsEndDateTestCase(TestCase):
    @mock_session(**{"get.return_value.text": test_timeseries_csv_bottom})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.result = self.client.get_ts_end_date(41, 42, 43)

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/api/stations/41/timeseriesgroups/42/timeseries/43/"
            "bottom/"
        )

    def test_returns_date(self):
        self.assertEqual(self.result, dt.datetime(2014, 1, 5, 8, 0))


class GetTsEndDateErrorTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            client.get_ts_end_date(41, 42, 43)


class GetTsEndDateEmptyTestCase(TestCase):
    @mock_session(**{"get.return_value.text": ""})
    def test_returns_date(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        date = client.get_ts_end_date(41, 42, 43)
        self.assertIsNone(date)
