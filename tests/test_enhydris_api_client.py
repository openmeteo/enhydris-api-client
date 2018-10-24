import textwrap
from datetime import datetime
from io import StringIO
from unittest import TestCase, mock

import pandas as pd
import requests

import enhydris_api_client


class SimpleLoginTestCase(TestCase):
    @mock.patch(
        "requests.get", **{"return_value.cookies": {"csrftoken": "reallysecret"}}
    )
    @mock.patch(
        "requests.post", **{"return_value.cookies": {"acookie": "a cookie value"}}
    )
    def setUp(self, mock_requests_post, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.mock_requests_post = mock_requests_post
        self.response_cookies = enhydris_api_client.login(
            "https://mydomain.com", "admin", "topsecret"
        )

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

    def test_checks_response_code_for_get(self):
        self.mock_requests_get.return_value.raise_for_status.assert_called_once_with()

    def test_checks_response_code_for_post(self):
        self.mock_requests_post.return_value.raise_for_status.assert_called_once_with()

    def test_returns_cookies(self):
        self.assertEqual(self.response_cookies, {"acookie": "a cookie value"})


class LoginWithEmptyUsernameTestCase(TestCase):
    @mock.patch("requests.get")
    @mock.patch("requests.post")
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
    @mock.patch(
        "requests.get", **{"return_value.json.return_value": {"hello": "world"}}
    )
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.response_data = enhydris_api_client.get_model(
            "https://mydomain.com", {"acookie": "a cookie value"}, "Station", 42
        )

    def test_makes_request(self):
        self.mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/Station/42/",
            cookies={"acookie": "a cookie value"},
        )

    def test_checks_response_code(self):
        self.mock_requests_get.return_value.raise_for_status.assert_called_once_with()

    def test_returns_data(self):
        self.assertEqual(self.response_data, {"hello": "world"})


class PostModelTestCase(TestCase):
    @mock.patch("requests.post", **{"return_value.json.return_value": {"id": 42}})
    def setUp(self, mock_requests_post):
        self.mock_requests_post = mock_requests_post
        self.response_data = enhydris_api_client.post_model(
            "https://mydomain.com",
            {"csrftoken": "reallysecret"},
            "Station",
            data={"location": "Syria"},
        )

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

    def test_checks_response_code(self):
        self.mock_requests_post.return_value.raise_for_status.assert_called_once_with()

    def test_returns_id(self):
        self.assertEqual(self.response_data, 42)


class DeleteModelTestCase(TestCase):
    @mock.patch("requests.delete", **{"return_value.status_code": 204})
    def test_makes_request(self, mock_requests_delete):
        enhydris_api_client.delete_model(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, "Station", 42
        )
        mock_requests_delete.assert_called_once_with(
            "https://mydomain.com/api/Station/42/",
            headers={"X-CSRFToken": "reallysecret"},
            cookies={"csrftoken": "reallysecret"},
        )

    @mock.patch("requests.delete", **{"return_value.status_code": 404})
    def test_raises_exception_on_error(self, mock_requests_delete):
        with self.assertRaises(requests.exceptions.HTTPError):
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
    @mock.patch("requests.get", **{"return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.response_data = enhydris_api_client.read_tsdata(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )

    def test_makes_request(self):
        self.mock_requests_get.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/", cookies={"csrftoken": "reallysecret"}
        )

    def test_checks_response_code(self):
        self.mock_requests_get.return_value.raise_for_status.assert_called_once_with()

    def test_returns_data(self):
        pd.testing.assert_frame_equal(self.response_data, test_timeseries_pd)


class PostTsDataTestCase(TestCase):
    @mock.patch("requests.post")
    def setUp(self, mock_requests_post):
        self.mock_requests_post = mock_requests_post
        enhydris_api_client.post_tsdata(
            "https://mydomain.com",
            {"csrftoken": "reallysecret"},
            42,
            test_timeseries_pd,
        )

    def test_makes_request(self):
        f = StringIO()
        test_timeseries_pd.to_csv(f, header=False)
        self.mock_requests_post.assert_called_once_with(
            "https://mydomain.com/api/tsdata/42/",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": "reallysecret",
            },
            cookies={"csrftoken": "reallysecret"},
            data={"timeseries_records": f.getvalue()},
        )

    def test_checks_response_code(self):
        self.mock_requests_post.return_value.raise_for_status.assert_called_once_with()


class GetTsEndDateTestCase(TestCase):
    @mock.patch("requests.get", **{"return_value.text": test_timeseries_csv})
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.response_date = enhydris_api_client.get_ts_end_date(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )

    def test_makes_request(self):
        self.mock_requests_get.assert_called_once_with(
            "https://mydomain.com/timeseries/d/42/bottom/",
            cookies={"csrftoken": "reallysecret"},
        )

    def test_checks_response_code(self):
        self.mock_requests_get.return_value.raise_for_status.assert_called_once_with()

    def test_returns_date(self):
        self.assertEqual(self.response_date, datetime(2014, 1, 5, 8, 0))


class GetTsEndDateEmptyTestCase(TestCase):
    @mock.patch("requests.get", **{"return_value.text": ""})
    def setUp(self, mock_requests_get):
        self.mock_requests_get = mock_requests_get
        self.response_date = enhydris_api_client.get_ts_end_date(
            "https://mydomain.com", {"csrftoken": "reallysecret"}, 42
        )

    def test_returns_date(self):
        self.assertEqual(self.response_date, datetime(1, 1, 1))
