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

Example
=======

::

    from enhydris_api_client import EnhydrisApiClient

    api_client = EnhydrisApiClient("https://openmeteo.org")
    api_client.login("joe", "topsecret")

    # Get a dict with attrs of station with id=42
    station = api_client.get_model(Station, 42)

    # Create a new station
    api_client.post_model(Station, data={"name": "my station"})


Reference
=========

**EnhydrisApiClient(base_url)**

    Creates a client. It has the following methods.

**.login(username, password)**

    Logins to Enhydris. Raises an exception if unsuccessful.

**.get_model(model, id)**

    Returns a dict with the data for the model of type ``model`` (a string such
    as "Timeseries" or "Station"), with the given ``id``.

**.post_model(model, data)**

    Creates a new model of type ``model`` (a string such as "Timeseries"
    or "Station"), with its data given by dictionary ``data``, and
    returns its id.

**.delete_model(model, id)**

    Deletes the specified model. See ``get_model`` for the parameters.

**.read_tsdata(timeseries_id)**

    Retrieves the time series data into a pandas dataframe indexed by date that
    it returns.

**.post_tsdata(timeseries_id, ts)**

    Posts a time series to Enhydris "api/tsdata", appending the records
    to any already existing. ``ts`` is a pandas dataframe indexed by date.

**.get_ts_end_date(ts_id)**

    Returns a ``datetime`` object which is the last timestamp of the time
    series. If the time series is empty, it returns a ``datetime`` object
    that corresponds to 1 January 0001 00:00.
