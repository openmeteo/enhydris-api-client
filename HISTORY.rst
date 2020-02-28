=======
History
=======

1.0.0 (2020-02-28)
==================

- We now support only Python 3.7 or greater.
- If there is an http error, the error message now includes the response body.

0.5.1 (2020-01-05)
==================

- Minor fix for compatibility with htimeseries 2

0.5.0 (2019-06-13)
==================

- Can now be used as a context manager
- Added post/put/patch/delete station

0.4.1 (2019-06-12)
==================

- Fixed bug where .read_tsdata() was failing to set the metadata
  attributes of the time series.

0.4.0 (2019-06-12)
==================

- .read_tsdata() now accepts optional arguments start_date and end_date.

0.3.0 (2019-06-06)
==================

- Upgrade dependecy htimeseries to 1.0

0.2.0 (2019-04-17)
==================

- Support new API of Enhydris 3

0.1.0 (2019-03-06)
==================

- Initial release
