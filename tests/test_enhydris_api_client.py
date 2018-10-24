import textwrap
from datetime import datetime
from io import StringIO
from unittest import TestCase, mock

import pandas as pd
import requests

import enhydris_api_client


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


class SimpleLoginTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post")
    def test_makes_post_request(self, mock_requests_post, mock_requests_get):
        enhydris_api_client.login("https://mydomain.com", "admin", "topsecret")
        mock_requests_post.assert_called_once_with(
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

    @rpatch("requests.get", **{"return_value.status_code": 404})
    @rpatch("requests.post")
    def test_checks_response_code_for_get(self, mock_requests_post, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.login("https://mydomain.com", "admin", "topsecret")

    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.status_code": 404})
    def test_checks_response_code_for_post(self, mock_requests_post, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.login("https://mydomain.com", "admin", "topsecret")

    @rpatch("requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}})
    @rpatch("requests.post", **{"return_value.cookies": {"acookie": "a cookie value"}})
    def test_returns_cookies(self, mock_requests_post, mock_requests_get):
        c = enhydris_api_client.login("https://mydomain.com", "admin", "topsecret")
        self.assertEqual(c, {"acookie": "a cookie value"})


class LoginWithEmptyUsernameTestCase(TestCase):
    @rpatch("requests.get")
    @rpatch("requests.post")
    def setUp(self, mock_requests_post, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.mock_requests_post = mock_requests_post
        self.response_cookies = enhydris_api_client.login(
            "https://mydomain.com", "", "useless_password"
        )

    def test_does_not_make_get_request(self):
        self.mock_requests_get.assert_not_called()

    def test_does_not_make_post_request(self):
        self.mock_requests_post.assert_not_called()

    def test_returns_empty(self):
        self.assertEqual(self.response_cookies, {})


class GetModelTestCase(TestCase):
    @rpatch("requests.get")
    def test_makes_request(self, mock_requests_get):
        enhydris_api_client.get_model(
            "https://mydomain.com", {"acookie": "a cookie value"}, "Station", 42
        )
        mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/Station/42/",
            cookies={"acookie": "a cookie value"},
        )

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.get_model(
                "https://mydomain.com", {"acookie": "a cookie value"}, "Station", 42
            )

    @rpatch("requests.get", **{"return_value.json.return_value": {"hello": "world"}})
    def test_returns_data(self, mock_requests_get):
        data = enhydris_api_client.get_model("https://mydomain.com", {}, "Station", 42)
        self.assertEqual(data, {"hello": "world"})


class PostModelTestCase(TestCase):
    @rpatch("requests.post", **{"return_value.json.return_value": {"id": 42}})
    def test_makes_request(self, mock_requests_post):
        enhydris_api_client.post_model(
            "https://mydomain.com",
            {"csrftoken": "reallysecret"},
            "Station",
            data={"location": "Syria"},
        )
        mock_requests_post.assert_called_once_with(
            "https://mydomain.com/api/Station/",
            headers={
                "X-CSRFToken": "reallysecret",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            cookies={"csrftoken": "reallysecret"},
            data={"location": "Syria"},
        )

    @rpatch("requests.post", **{"return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_post):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.post_model(
                "https://mydomain.com",
                {"csrftoken": "reallysecret"},
                "Station",
                data={"location": "Syria"},
            )

    @rpatch("requests.post", **{"return_value.json.return_value": {"id": 42}})
    def test_returns_id(self, mock_requests_post):
        r = enhydris_api_client.post_model(
            "https://mydomain.com",
            {"csrftoken": "reallysecret"},
            "Station",
            data={"location": "Syria"},
        )
        self.assertEqual(r, 42)


class DeleteModelTestCase(TestCase):
    @rpatch("requests.delete", **{"return_value.status_code": 204})
    def test_makes_request(self, mock_requests_delete):
        enhydris_api_client.delete_model(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, "Station", 42
        )
        mock_requests_delete.assert_called_once_with(
            "https://mydomain.com/api/Station/42/",
            headers={"X-CSRFToken": "reallysecret"},
            cookies={"csrftoken": "reallysecret"},
        )

    @rpatch("requests.delete", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_delete):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.delete_model(
                "https://mydomain.com", {"csrftoken": "reallysecret"}, "Station", 42
            )


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
    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_makes_request(self, mock_requests_get):
        enhydris_api_client.read_tsdata(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )
        mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/", cookies={"csrftoken": "reallysecret"}
        )

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.read_tsdata(
                "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
            )

    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_returns_data(self, mock_requests_get):
        data = enhydris_api_client.read_tsdata(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )
        pd.testing.assert_frame_equal(data, test_timeseries_pd)


class PostTsDataTestCase(TestCase):
    @rpatch("requests.post")
    def test_makes_request(self, mock_requests_post):
        enhydris_api_client.post_tsdata(
            "https://mydomain.com",
            {"csrftoken": "reallysecret"},
            42,
            test_timeseries_pd,
        )
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
    def test_checks_response_code(self, mock_requests_post):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.post_tsdata(
                "https://mydomain.com",
                {"csrftoken": "reallysecret"},
                42,
                test_timeseries_pd,
            )


class GetTsEndDateTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_makes_request(self, mock_requests_get):
        enhydris_api_client.get_ts_end_date(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )
        mock_requests_get.assert_called_once_with(
            "https://mydomain.com/timeseries/d/42/bottom/",
            cookies={"csrftoken": "reallysecret"},
        )

    @rpatch("requests.get", **{"return_value.status_code": 404})
    def test_checks_response_code(self, mock_requests_get):
        with self.assertRaises(requests.HTTPError):
            enhydris_api_client.get_ts_end_date(
                "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
            )

    @rpatch("requests.get", **{"return_value.text": test_timeseries_csv})
    def test_returns_date(self, mock_requests_get):
        date = enhydris_api_client.get_ts_end_date(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )
        self.assertEqual(date, datetime(2014, 1, 5, 8, 0))


class GetTsEndDateEmptyTestCase(TestCase):
    @rpatch("requests.get", **{"return_value.text": ""})
    def test_returns_date(self, mock_requests_get):
        date = enhydris_api_client.get_ts_end_date(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )
        self.assertEqual(date, datetime(1, 1, 1))
