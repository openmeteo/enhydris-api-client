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

    with EnhydrisApiClient("https://openmeteo.org", "my_auth_token") as api_client:
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

Not specifying ``token`` is deprecated. ``token`` will become mandatory
in future versions.

``EnhydrisApiClient`` objects have the following methods:

**.get_token(username, password)**

(Deprecated.) Gets an API token from Enhydris and thereafter uses it in
subsequent requests. The method will be removed in future versions.

| **.get_station(id)**
| **.post_station(data)**
| **.put_station(station_id, data)**
| **.patch_station(station_id, data)**
| **.delete_station(station_id)**

Methods that create, retrieve, update or delete stations. The ``data``
argument (for those methods that receive one) is a dictionary.
``get_station()`` returns a dictionary with the data for the station.
``post_station()`` returns the created station's id.

| **.list_timeseries(station_id, timeseries_group_id)**
| **.get_timeseries(station_id, timeseries_group_id, timeseries_id)**
| **.post_timeseries(station_id, timeseries_group_id, data)**
| **.delete_timeseries(station_id, timeseries_group_id, timeseries_id)**

Methods that create, retrieve or delete time series. Similar to the ones
for station. ``list_timeseries()`` returns a list of dictionaries.

| **.read_tsdata(station_id, timeseries_group_id, timeseries_id, start_date=None, end_date=None)**
| **.post_tsdata(station_id, timeseries_group_id, timeseries_id, ts)**
| **.get_ts_end_date(station_id, timeseries_group_id, timeseries_id)**

Methods that retrieve or update time series data.

``read_ts_data()`` retrieves the time series data into a htimeseries
object that it returns. If ``start_date`` and/or ``end_date`` are
specified, only the part of the time series between these dates is
retrieved.

``post_tsdata() `` posts a time series to Enhydris, appending the
records to any already existing.  ``ts`` is a htimeseries object.

``get_ts_end_date()`` returns a ``datetime`` object which is the last
timestamp of the time series. If the time series is empty it returns
``None``.
