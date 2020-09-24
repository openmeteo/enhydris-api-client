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

    with EnhydrisApiClient("https://openmeteo.org") as api_client:
        api_client.get_token("joe", "topsecret")

        # Get a dict with attrs of station with id=42
        station = api_client.get_model(Station, 42)

        # Create a new station
        api_client.post_model(Station, data={"name": "my station"})


Reference
=========

**EnhydrisApiClient(base_url, token=None)**

Creates and returns an api client. It can also be used as a context
manager, though this is not necessary. If not used as a context manager,
you might get warnings about unclosed sockets.

``EnhydrisApiClient`` objects have the following methods:

**.get_token(username, password)**

Logins to Enhydris and returns ``token``. Raises an exception if unsuccessful.

**.get_station(id)**

Returns a dict with the data for the station with the given ``id``.

**.post_station(data)**

Creates a new station, with its data given by dictionary ``data``, and
returns its id.

**.put_station(station_id, data)**

Replaces the station's attributes with ``data`` (a dictionary). Any
unspecified attributes are set to null.

**.patch_station(station_id, data)**

Same as ``put_station()`` except that any attribute not specified in
``data`` is untouched.

**.delete_station(station_id)**

Deletes the specified station.

**.list_timeseries(station_id, timeseries_group_id)**

Returns a list of time series in the specified group. Each item in the
list is a dict with the data for the time series.

**.get_timeseries(station_id, timeseries_group_id, timeseries_id)**

Returns a dict with the data for the given time series.

**.post_timeseries(station_id, timeseries_group_id, data)**

Creates a new time series, with its data given by dictionary ``data``,
and returns its id.

**.delete_timeseries(station_id, timeseries_group_id, timeseries_id)**

Deletes the specified time series.

**.read_tsdata(station_id, timeseries_group_id, timeseries_id, start_date=None, end_date=None)**

Retrieves the time series data into a htimeseries object that it
returns. If ``start_date`` and/or ``end_date`` are specified, only the
part of the time series between these dates is retrieved.

**.post_tsdata(station_id, timeseries_group_id, timeseries_id, ts)**

Posts a time series to Enhydris, appending the records to any already
existing.  ``ts`` is a htimeseries object.

**.get_ts_end_date(station_id, timeseries_group_id, timeseries_id)**

Returns a ``datetime`` object which is the last timestamp of the time
series. If the time series is empty it returns ``None``.
