import textwrap
from datetime import datetime
from io import StringIO
from unittest import TestCase, mock

import pandas as pd
import requests

from enhydris_api_client import EnhydrisApiClient


def rpatch(*args, **kwargs):
    """Same as mock.patch with raise_for_status feature.

    When mocking requests.get or requests.post or similar, instead of
        @mock.patch("requests.get", ...)
    use
        @rpatch("requests.get", ...)

    It's almost the same thing. There are two differences:
        - If "return_value.status_code" is unspecified, it is set to 200.
        - If "return_value.status_code" is not between 200 and 400, then
          return_value.raise_for_status() will raise HTTPError. This will only work if
          "return_value.status_code" is specified in kwargs.
    """
    c = kwargs.setdefault("return_value.status_code", 200)
    if c < 200 or c >= 400:
        kwargs["return_value.raise_for_status.side_effect"] = requests.HTTPError
    return mock.patch(*args, **kwargs)


class SuccessfulLoginTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.cookies": {"acookie": "a cookie value"}})
    def setUp(self, mock_requests_post, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.mock_requests_post = mock_requests_post
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login("admin", "topsecret")

    def test_makes_post_request(self):
        self.mock_requests_post.assert_called_once_with(
            "https://mydomain.com/accounts/login/",
            headers={
                "X-CSRFToken": "reallysecret",
                "Referer": "https://mydomain.com/accounts/login/",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="username=admin&password=topsecret",
            cookies={"csrftoken": "reallysecret"},
            allow_redirects=False,
        )

    def test_keeps_cookies(self):
        self.assertEqual(self.client.cookies, {"acookie": "a cookie value"})


class FailedLoginTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.get", **{"return_value.status_code": 404})
    @rpatch("requests.post")
    def test_raises_exception_on_get_failure(self, mock_post, mock_get):
        with self.assertRaises(requests.HTTPError):
            self.client.login("admin", "topsecret")

    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.status_code": 404})
    def test_raises_exception_on_post_failure(self, mock_post, mock_get):
        with self.assertRaises(requests.HTTPError):
            self.client.login("admin", "topsecret")


class LoginWithEmptyUsernameTestCase(TestCase):
    @rpatch("requests.get")
    @rpatch("requests.post")
    def setUp(self, mock_requests_post, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.mock_requests_post = mock_requests_post
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login("", "useless_password")

    def test_does_not_make_get_request(self):
        self.mock_requests_get.assert_not_called()

    def test_does_not_make_post_request(self):
        self.mock_requests_post.assert_not_called()

    def test_no_cookies_set(self):
        self.assertEqual(self.client.cookies, {})


class GetModelTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.json.return_value": {"hello": "world"}})
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.data = self.client.get_model("Station", 42)

    def test_makes_request(self):
        self.mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/Station/42/", cookies={}
        )

    def test_returns_data(self):
        self.assertEqual(self.data, {"hello": "world"})


class GetModelErrorTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            self.data = self.client.get_model("Station", 42)


class PostModelTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

        # Login
        kwargs = {"return_value.cookies": {"csrftoken": "reallysecret"}}
        with rpatch("requests.post", **kwargs), rpatch("requests.get", **kwargs):
            self.client.login(username="admin", password="topsecret")

        # Post model
        kwargs = {"return_value.json.return_value": {"id": 42}}
        with rpatch("requests.post", **kwargs) as p:
            self.mock_requests_post = p
            self.data = self.client.post_model("Station", data={"location": "Syria"})

    def test_makes_request(self):
        self.mock_requests_post.assert_called_once_with(
            "https://mydomain.com/api/Station/",
            headers={
                "X-CSRFToken": "reallysecret",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            cookies={"csrftoken": "reallysecret"},
            data={"location": "Syria"},
        )

    def test_returns_id(self):
        self.assertEqual(self.data, 42)


class FailedPostModelTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.post", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_post):
        with self.assertRaises(requests.HTTPError):
            self.client.post_model("Station", data={"location": "Syria"})


class DeleteModelTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    def setUp(self, mrp, mrg):
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login(username="admin", password="topsecret")

    @rpatch("requests.delete", **{"return_value.status_code": 204})
    def test_makes_request(self, mock_requests_delete):
        self.client.delete_model("Station", 42)
        mock_requests_delete.assert_called_once_with(
            "https://mydomain.com/api/Station/42/",
            headers={"X-CSRFToken": "reallysecret"},
            cookies={"csrftoken": "reallysecret"},
        )

    @rpatch("requests.delete", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_delete):
        with self.assertRaises(requests.HTTPError):
            self.client.delete_model("Station", 42)


test_timeseries_csv = textwrap.dedent(
    """\
    2014-01-01 08:00,11,
    2014-01-02 08:00,12,
    2014-01-03 08:00,13,
    2014-01-04 08:00,14,
    2014-01-05 08:00,15,
    """
)
test_timeseries_pd = pd.read_csv(
    StringIO(test_timeseries_csv), header=None, parse_dates=True, index_col=0
)
test_timeseries_csv_top = "".join(test_timeseries_csv.splitlines(keepends=True)[:-1])
test_timeseries_csv_bottom = test_timeseries_csv.splitlines(keepends=True)[-1][0]


class ReadTsDataTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_makes_request(self, mock_requests_get):
        self.client.read_tsdata(42)
        mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/", cookies={}
        )

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            self.client.read_tsdata(42)

    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_returns_data(self, mock_requests_get):
        data = self.client.read_tsdata(42)
        pd.testing.assert_frame_equal(data, test_timeseries_pd)


class PostTsDataTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    def setUp(self, mrp, mrg):
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.client.login(username="admin", password="topsecret")

    @rpatch("requests.post")
    def test_makes_request(self, mock_requests_post):
        self.client.post_tsdata(42, test_timeseries_pd)
        f = StringIO()
        test_timeseries_pd.to_csv(f, header=False)
        mock_requests_post.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": "reallysecret",
            },
            cookies={"csrftoken": "reallysecret"},
            data={"timeseries_records": f.getvalue()},
        )

    @rpatch("requests.post", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_post):
        with self.assertRaises(requests.HTTPError):
            self.client.post_tsdata(42, test_timeseries_pd)


class GetTsEndDateTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.client = EnhydrisApiClient("https://mydomain.com")
        self.result = self.client.get_ts_end_date(42)

    def test_makes_request(self):
        self.mock_requests_get.assert_called_once_with(
            "https://mydomain.com/timeseries/d/42/bottom/", cookies={}
        )

    def test_returns_date(self):
        self.assertEqual(self.result, datetime(2014, 1, 5, 8, 0))


class GetTsEndDateErrorTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            self.client.get_ts_end_date(42)


class GetTsEndDateEmptyTestCase(TestCase):
    def setUp(self):
        self.client = EnhydrisApiClient("https://mydomain.com")

    @rpatch("requests.get", **{"return_value.text": ""})
    def test_returns_date(self, mock_requests_get):
        date = self.client.get_ts_end_date(42)
        self.assertEqual(date, datetime(1, 1, 1))
