import json
import os
import textwrap
from datetime import datetime
from io import StringIO
from unittest import skipUnless, TestCase, mock

import pandas as pd
import requests

from enhydris_api_client import EnhydrisApiClient


def mock_session(**kwargs):
    """Mock requests.Session.

    Returns
        @mock.patch("requests.Session", modified_kwargs)

    However, it first tampers with kwargs in order to achieve the following:
    - It adds a leading "return_value." to the kwargs; so you don't need to specify,
      for example, "return_value.get.return_value", you just specify "get.return_value".
    - If kwargs doesn't contain "get.return_value.status_code", it adds
      a return code of 200. Likewise for post, put and patch. For delete it's 204.
    - If "get.return_value.status_code" is not between 200 and 399,
      then raise_for_status() will raise HTTPError. Likewise for the other methods.
    """
    for method in ("get", "post", "put", "patch", "delete"):
        default_value = 204 if method == "delete" else 200
        c = kwargs.setdefault(method + ".return_value.status_code", default_value)
        if c < 200 or c >= 400:
            method_side_effect = method + ".return_value.raise_for_status.side_effect"
            kwargs[method_side_effect] = requests.HTTPError
    for old_key in list(kwargs.keys()):
        kwargs["return_value." + old_key] = kwargs.pop(old_key)
    return mock.patch("requests.Session", **kwargs)


class SuccessfulLoginTestCase(TestCase):
    @mock_session(
        **{
            "get.return_value.cookies": {"csrftoken": "reallysecret"},
            "post.return_value.cookies": {"acookie": "a cookie value"},
        }
    )
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login("admin", "topsecret")

    def test_makes_post_request(self):
        self.mock_requests_session.return_value.post.assert_called_once_with(
            "https://mydomain.com/accounts/login/",
            data="username=admin&password=topsecret",
            allow_redirects=False,
        )


class FailedLoginTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def test_raises_exception_on_get_failure(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            self.client.login("admin", "topsecret")

    @mock_session(**{"post.return_value.status_code": 404})
    def test_raises_exception_on_post_failure(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            self.client.login("admin", "topsecret")


class LoginWithEmptyUsernameTestCase(TestCase):
    @mock_session()
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login("", "useless_password")

    def test_does_not_make_get_request(self):
        self.mock_requests_session.get.assert_not_called()

    def test_does_not_make_post_request(self):
        self.mock_requests_session.post.assert_not_called()


class GetModelTestCase(TestCase):
    @mock_session(**{"get.return_value.json.return_value": {"hello": "world"}})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.get_model("Station", 42)

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/api/Station/42/"
        )

    def test_returns_data(self):
        self.assertEqual(self.data, {"hello": "world"})


class GetModelErrorTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def setUp(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")

    def test_raises_exception_on_error(self):
        with self.assertRaises(requests.HTTPError):
            self.data = self.client.get_model("Station", 42)


class PostModelTestCase(TestCase):
    @mock_session(**{"post.return_value.json.return_value": {"id": 42}})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.post_model("Station", data={"location": "Syria"})

    def test_makes_request(self):
        self.mock_requests_session.return_value.post.assert_called_once_with(
            "https://mydomain.com/api/Station/", data={"location": "Syria"}
        )

    def test_returns_id(self):
        self.assertEqual(self.data, 42)


class FailedPostModelTestCase(TestCase):
    @mock_session(**{"post.return_value.status_code": 404})
    def setUp(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")

    def test_raises_exception_on_error(self):
        with self.assertRaises(requests.HTTPError):
            self.client.post_model("Station", data={"location": "Syria"})


class DeleteModelTestCase(TestCase):
    @mock_session()
    def test_makes_request(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.delete_model("Station", 42)
        mock_requests_session.return_value.delete.assert_called_once_with(
            "https://mydomain.com/api/Station/42/"
        )

    @mock_session(**{"delete.return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_delete):
        self.client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            self.client.delete_model("Station", 42)


test_timeseries_csv = textwrap.dedent(
    """\
    2014-01-01 08:00,11.0,
    2014-01-02 08:00,12.0,
    2014-01-03 08:00,13.0,
    2014-01-04 08:00,14.0,
    2014-01-05 08:00,15.0,
    """
)
test_timeseries_pd = pd.read_csv(
    StringIO(test_timeseries_csv), header=None, parse_dates=True, index_col=0
)
test_timeseries_csv_top = "".join(test_timeseries_csv.splitlines(keepends=True)[:-1])
test_timeseries_csv_bottom = test_timeseries_csv.splitlines(keepends=True)[-1][0]


class ReadTsDataTestCase(TestCase):
    @mock_session(**{"get.return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.read_tsdata(42)

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/"
        )

    def test_returns_data(self):
        pd.testing.assert_frame_equal(self.data, test_timeseries_pd)


class ReadTsDataErrorTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_session):
        self.client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            self.client.read_tsdata(42)


class PostTsDataTestCase(TestCase):
    @mock_session()
    def test_makes_request(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        client.post_tsdata(42, test_timeseries_pd)
        f = StringIO()
        test_timeseries_pd.to_csv(f, header=False)
        mock_requests_session.return_value.post.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/",
            data={"timeseries_records": f.getvalue()},
        )

    @mock_session(**{"post.return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            client.post_tsdata(42, test_timeseries_pd)


class GetTsEndDateTestCase(TestCase):
    @mock_session(**{"get.return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_session):
        self.mock_requests_session = mock_requests_session
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.result = self.client.get_ts_end_date(42)

    def test_makes_request(self):
        self.mock_requests_session.return_value.get.assert_called_once_with(
            "https://mydomain.com/timeseries/d/42/bottom/"
        )

    def test_returns_date(self):
        self.assertEqual(self.result, datetime(2014, 1, 5, 8, 0))


class GetTsEndDateErrorTestCase(TestCase):
    @mock_session(**{"get.return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        with self.assertRaises(requests.HTTPError):
            client.get_ts_end_date(42)


class GetTsEndDateEmptyTestCase(TestCase):
    @mock_session(**{"get.return_value.text": ""})
    def test_returns_date(self, mock_requests_session):
        client = EnhydrisApiClient("https://mydomain.com")
        date = client.get_ts_end_date(42)
        self.assertEqual(date, datetime(1, 1, 1))


@skipUnless(
    os.getenv("ENHYDRIS_API_CLIENT_E2E_TEST"), "Set ENHYDRIS_API_CLIENT_E2E_TEST"
)
class EndToEndTestCase(TestCase):
    """End-to-end test against a real Enhydris instance.
    To execute this test, specify the ENHYDRIS_API_CLIENT_E2E_TEST environment variable
    like this:
        ENHYDRIS_API_CLIENT_E2E_TEST='
            {"base_url": "http://localhost:8001",
             "username": "admin",
             "password": "topsecret",
             "owner_id": 9,
             "stype_id": 1,
             "time_zone_id": 3,
             "unit_of_measurement_id": 18,
             "variable_id": 22,
             }
        '
    This should point to an Enhydris server. Avoid using a production database for
    that; the testing functionality will write objects to the database. Although
    things are normally cleaned up (created objects will be deleted), id serial
    numbers will be affected and things might not be cleaned up if there is an error.

    It would be better to specify only base_url, username and password, and let the
    test create a user, a station type, a time zone, etc. However the Enhydris API
    currently does not allow creation of these types.
    """

    def setUp(self):
        v = json.loads(os.getenv("ENHYDRIS_API_CLIENT_E2E_TEST"))
        self.client = EnhydrisApiClient(v["base_url"])
        self.username = v["username"]
        self.password = v["password"]
        self.stype_id = v["stype_id"]
        self.owner_id = v["owner_id"]
        self.time_zone_id = v["time_zone_id"]
        self.unit_of_measurement_id = v["unit_of_measurement_id"]
        self.variable_id = v["variable_id"]

    def tearDown(self):
        self.remove_item("Timeseries")
        self.remove_item("Station")

    def remove_item(self, itemtype):
        id_attribute = itemtype.lower() + "_id"
        id_value = getattr(self, id_attribute, None)
        if id_value:
            self.client.delete_model(itemtype, id_value)

    def test_e2e(self):
        # Verify we are logged out
        r = self.client.session.get(self.client.base_url)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Login" in r.text)
        self.assertFalse("Logout" in r.text)

        # Login and verify we're logged on
        self.client.login(self.username, self.password)
        r = self.client.session.get(self.client.base_url)
        self.assertEqual(r.status_code, 200)
        self.assertFalse("Login" in r.text)
        self.assertTrue("Logout" in r.text)

        # Create a station and verify it was created
        self.station_id = self.client.post_model(
            "Station",
            data={
                "name": "Delete me",
                "copyright_holder": "Joe",
                "copyright_years": "2018",
                "owner": self.owner_id,
                "stype": [self.stype_id],
            },
        )
        station = self.client.get_model("Station", self.station_id)
        self.assertEqual(station["name"], "Delete me")

        # Create a time series and verify it was created
        self.timeseries_id = self.client.post_model(
            "Timeseries",
            data={
                "name": "Delete this time series",
                "gentity": self.station_id,
                "time_zone": self.time_zone_id,
                "unit_of_measurement": self.unit_of_measurement_id,
                "variable": self.variable_id,
            },
        )
        timeseries = self.client.get_model("Timeseries", self.timeseries_id)
        self.assertEqual(timeseries["name"], "Delete this time series")

        # Post time series data
        self.client.post_tsdata(self.timeseries_id, test_timeseries_pd)

        # Get the last date and check it
        date = self.client.get_ts_end_date(self.timeseries_id)
        self.assertEqual(date, datetime(2014, 1, 5, 8, 0))

        # Get all time series data and check it
        data = self.client.read_tsdata(self.timeseries_id)
        pd.testing.assert_frame_equal(data, test_timeseries_pd)
