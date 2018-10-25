from datetime import datetime
from io import StringIO
from urllib.parse import urljoin

import iso8601
import pandas as pd
import requests


# My understanding from requests' documentation is that when I make a post
# request, it shouldn't be necessary to specify Content-Type:
# application/x-www-form-urlencoded, and that requests adds the header
# automatically. However, when running in Python 3, apparently requests does
# not add the header (although it does convert the post data to
# x-www-form-urlencoded format). This is why the header has been explicitly
# specified in all post requests.


class EnhydrisApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.cookies = {}

    def login(self, username, password):
        self.cookies = {}
        if not username:
            return
        login_url = urljoin(self.base_url, "accounts/login/")
        r = requests.get(login_url)
        r.raise_for_status()
        r1 = requests.post(
            login_url,
            headers={
                "X-CSRFToken": r.cookies.get("csrftoken", "unspecified CSRF token"),
                "Referer": login_url,
                "Content-Type": "application/x-www-form-urlencoded"
                # See comment about x-www-form-urlencoded above
            },
            data="username={}&password={}".format(username, password),
            cookies=r.cookies,
            allow_redirects=False,
        )
        r1.raise_for_status()
        self.cookies = r1.cookies

    def get_model(self, model, obj_id):
        url = urljoin(self.base_url, "api/{}/{}/".format(model, obj_id))
        r = requests.get(url, cookies=self.cookies)
        r.raise_for_status()
        return r.json()

    def post_model(self, model, data):
        r = requests.post(
            urljoin(self.base_url, "api/{}/".format(model)),
            headers={
                "X-CSRFToken": self.cookies.get("csrftoken", "unspecified CSRF token"),
                "Content-Type": "application/x-www-form-urlencoded"
                # See comment about x-www-form-urlencoded above
            },
            cookies=self.cookies,
            data=data,
        )
        r.raise_for_status()
        return r.json()["id"]

    def delete_model(self, model, id):
        url = urljoin(self.base_url, "api/{}/{}/".format(model, id))
        r = requests.delete(
            url,
            cookies=self.cookies,
            headers={"X-CSRFToken": self.cookies["csrftoken"]},
        )
        if r.status_code != 204:
            raise requests.HTTPError()

    def read_tsdata(self, ts_id):
        url = urljoin(self.base_url, "api/tsdata/{0}/".format(ts_id))
        r = requests.get(url, cookies=self.cookies)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text), header=None, parse_dates=True, index_col=0)

    def post_tsdata(self, timeseries_id, ts):
        f = StringIO()
        ts.to_csv(f, header=False)
        url = urljoin(self.base_url, "api/tsdata/{}/".format(timeseries_id))
        r = requests.post(
            url,
            data={"timeseries_records": f.getvalue()},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": self.cookies.get("csrftoken"),
            },
            cookies=self.cookies,
        )
        r.raise_for_status()
        return r.text

    def get_ts_end_date(self, ts_id):
        url = urljoin(self.base_url, "timeseries/d/{}/bottom/".format(ts_id))
        r = requests.get(url, cookies=self.cookies)
        r.raise_for_status()
        lines = r.text.splitlines()
        lines.reverse()
        for line in [x.strip() for x in lines]:
            if not line:
                continue
            datestring = line.split(",")[0]
            return iso8601.parse_date(datestring, default_timezone=None)
        return datetime(1, 1, 1)
