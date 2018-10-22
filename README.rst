===================
enhydris-api-client
===================


.. image:: https://img.shields.io/pypi/v/enhydris_api_client.svg
        :target: https://pypi.python.org/pypi/enhydris-api-client
        :alt: Pypi

.. image:: https://img.shields.io/travis/openmeteo/enhydris-api-client.svg
        :target: https://travis-ci.org/openmeteo/enhydris-api-client
        :alt: Build

.. image:: https://codecov.io/github/openmeteo/enhydris-api-client/coverage.svg
        :target: https://codecov.io/gh/openmeteo/enhydris-api-client
        :alt: Coverage

.. image:: https://pyup.io/repos/github/openmeteo/enhydris-api-client/shield.svg
         :target: https://pyup.io/repos/github/openmeteo/enhydris-api-client/
         :alt: Updates

Python API client for Enhydris

* Free software: GNU General Public License v3

This package has some functionality to make it easier to use the
Enhydris API.

Installation
============

``pip install enhydris-api-client``

Reference
=========

**login(base_url, username, password)**

    Logins to Enhydris and returns a dictionary containing cookies.
    ``username`` can be a false value (``None`` or ``""``, for example), in
    which case an empty dictionary is returned.

    Example::

       import requests
       from pthelma import enhydris_api

       ...

       base_url = "https://openmeteo.org/"
       session_cookies = enhydris_api.login(base_url, "admin", "topsecret")

       # The following is a logged on request
       r = requests.get("https://openmeteo.org/api/Station/1334/", cookies=session_cookies)

       # But you would normally write it like this:
       mydict = enhydris_api.get_model(base_url, session_cookies, "Station", 1334)
      
       # If the request requires a CSRF token, a header must be added
       r = requests.post(
               "https://openmeteo.org/api/Timeseries/1825/",
               cookies=session_cookies,
               headers={
                   "Content-type": "application/json",
                   "X-CSRFToken": session_cookies["csrftoken"],
               },
               data=timeseries_json,
           )
       ts_id = r.text

       # But normally you don't need to worry because you'd write it like this:
       ts_id = enhydris_api.post_model(
           base_url, session_cookies, Timeseries, timeseries_json
       )

**get_model(base_url, session_cookies, model, id)**

    Returns json data for the model of type ``model`` (a string such as
    "Timeseries" or "Station"), with the given ``id``.

**post_model(base_url, session_cookies, model, data)**

    Creates a new model of type ``model`` (a string such as "Timeseries"
    or "Station"), with its data given by dictionary ``data``, and
    returns its id.

**delete_model(base_url, session_cookies, model, id)**

    Deletes the specified model. See ``get_model`` for the parameters.

**read_tsdata(base_url, session_cookies)**

    Retrieves the time series data into a pandas dataframe indexed by date that
    it returns.

**post_tsdata(base_url, session_cookies, timeseries_id, ts)**

    Posts a time series to Enhydris "api/tsdata", appending the records
    to any already existing. ``session_cookies`` is the value returned
    from ``.login``; ``ts`` is a pandas dataframe indexed by date.

**get_ts_end_date(base_url, session_cookies, ts_id)**

    Returns a ``datetime`` object which is the last timestamp of the time
    series. If the time series is empty, it returns a ``datetime`` object
    that corresponds to 1 January 0001 00:00.

**urljoin(*args)**

    This is a helper function intended to be used mostly internally. It
    concatenates its arguments separating them with slashes, but
    removes trailing slashes if this would result in double slashes;
    for example::

       >>> urljoin("http://openmeteo.org", "path/")
       'http://openmeteo.org/path/'
       >>> urljoin("http://openmeteo.org/", "path/")
       'http://openmeteo.org/path/'
