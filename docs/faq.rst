.. _faq:

Frequently Asked Questions
==========================

This part of the documentation answers common questions about the NPO Backstage API.

.. _date_granularity:

What does ``date_granularity`` mean?
------------------------------------
Dates are fickle things. A date is a particular point in time, and can be represented in `very many ways <http://xkcd.com/1179/>`_. In addition, dates have gradations in precision. For example, ``Jan. 1970`` is not as precise as ``1 January 1970 00:00:00`` is.

The different data sources in the NPO Backstage API expose dates with very different precisions (``Vr 20 mei 2015 18:00``, ``1 January 2010``, etc.), often because that is as precise as the collection owner *knows*. In order to be able to reason about these dates, we opted to generate a full-fledged date anyway (so ``Jan. 2010`` becomes ``2010-01-01:00:00:00``), and store its ``granularity`` alongside it. The granularity signifies how **precise** the date is known; it is an integer, which indicates *how many digits* of the (IS-formatted) date were known.

+----------------+----------------+---------------------------------------------------------+
| Example date   | Granularity    | Description                                             |
+================+================+=========================================================+
| 21th century   | 2              | ``21th century`` means ``between 2000 and 2100``        |
+----------------+----------------+---------------------------------------------------------+
| 2010           | 4              | We know the year exactly, so we know the first 4 digits |
+----------------+----------------+---------------------------------------------------------+
| January 2010   | 6              | Month and year                                          |
+----------------+----------------+---------------------------------------------------------+
| 1 January 2010 | 8              | Day, month and year                                     |
+----------------+----------------+---------------------------------------------------------+
