.. _restapi:

RESTful API
===========

.. warning::

   This page currently shows a draft of the API specification. **The format of some of the request/response pairs is still subject to change!**

General notes
-------------

The API accepts requests with JSON content and returns JSON data in all of its responses (unless stated otherwise). Standard HTTP response codes are used to indicate errors. In case of an error, a more detailed description can be found in the JSON response body. UTF-8 character encoding is used in both requests and responses.

All API URLs referenced in this documentation start with the following base part:

    :rest_api_v0:`v0`

.. warning::
   The URL of the API is currently http://backstage-api.openstate.eu, but will most likely change soon.

All API endpoints are designed according to the idea that there is an operation within a *context*: methods on the "root" context are executed across all datasets; :ref:`/search <rest_search>` executes a search across all data sources, whereas :ref:`/journalistiek/search <rest_source_search>` executes a search on the NPO Journalistiek data source.

Arguments to an endpoint are placed behind the method definition, or supplied as JSON in a POST request. For instance, the :ref:`similar objects endpoint <rest_similar>` can be executed within the context of a collection, and needs an ``object_id`` to execute on.

The ``object_id`` of in the PRID, metadata and TT888 datasets are based on their PRID, while the NPO Journalistiek ``object_id``'s are based on the OBEN IDs of each items. Their corresponding items in the combined index simply use the ``object_id`` prepended with the index name, e.g., an items ``object_id`` in the NPO Journalistiek index is ``Oben_290_40445`` and its ``object_id`` in the combined index is then ``journalistiek_Oben_290_40445``.

Collection overview and statistics
----------------------------------

.. http:get:: /sources

   Get a list of all available sources (collections) with item counts

   **Example request**

   .. sourcecode:: http

      $ curl -i -XGET 'http://backstage-api.openstate.eu/v0/sources'

   **Example response**

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-type: application/json
      Content-length: 369
      Date: Wed, 27 May 2015 12:36:15 GMT
      
      {
        "sources": [
          {
            "count": 24559, 
            "id": "npo_journalistiek", 
            "name": "NPO Journalistiek"
          }, 
          {
            "count": 3766, 
            "id": "metadata", 
            "name": "metadata"
          }, 
          {
            "count": 3766, 
            "id": "prid", 
            "name": "PRID"
          }, 
          {
            "count": 2483, 
            "id": "tt888", 
            "name": "tt888"
          }
        ]
      }

   :statuscode 200: OK, no errors.

.. _rest_search:

Searching within multiple collections
-------------------------------------

.. http:post:: /search

   Search for items through all indexed datasets.

   **Example request**

   .. sourcecode:: http

      $ curl -i -XPOST 'http://backstage-api.openstate.eu/v0/search' -d '{
         "query": "leenstelsel",
         "facets": {
            "collection": {},
            "date": {"interval": "day"}
         },
         "filters": {
            "media_content_type": {"terms": ["image/jpeg"]}
         },
         "size": 1
      }'

   **Example response**

    .. sourcecode:: http

      HTTP/1.1 200 OK
      content-type: application/json
      content-length: 3082
      date: Wed, 27 May 2015 12:41:45 GMT
      
      {
        "facets": {
          "collection": {
            "_type": "terms", 
            "missing": 0, 
            "other": 0, 
            "terms": [
              {
                "count": 11, 
                "term": "NPO Journalistiek"
              }
            ], 
            "total": 11
          }, 
          "date": {
            "_type": "date_histogram", 
            "entries": [
              {
                "count": 1, 
                "time": 1264982400000
              }, 
              {
                "count": 1, 
                "time": 1349049600000
              }, 
              {
                "count": 1, 
                "time": 1362096000000
              }, 
              {
                "count": 2, 
                "time": 1398902400000
              }, 
              {
                "count": 2, 
                "time": 1414800000000
              }, 
              {
                "count": 4, 
                "time": 1420070400000
              }
            ]
          }
        }, 
        "hits": {
          "hits": [
            {
              "_id": "journalistiek_Oben_290_40705", 
              "_score": 3.3434153, 
              "_source": {
                "authors": [
                  "KRO"
                ], 
                "date": "2013-03-12T09:30:00", 
                "date_granularity": 14, 
                "description": "<p>Het is na&iuml;ef als minister Jet Bussemaker van Onderwijs nog steeds gelooft dat het leenstelsel voor studenten er komt. Volgens de SP is inmiddels overduidelijk dat er geen meerderheid in de Eerste Kamer komt. En daarom moet Bussemaker stoppen met de voorbereidingen op het leenstelsel. Een gesprek met Tweede Kamerlid Jasper van Dijk van de SP.</p>", 
                "enrichments": {}, 
                "media_urls": [
                  {
                    "content_type": "image/jpeg", 
                    "height": 563, 
                    "url": "http://localhost:5000/v0/resolve/bfa42ec24cb23047f87cd9633fef34d2af6f3e0d", 
                    "width": 1000
                  }, 
                  {
                    "content_type": "image/jpeg", 
                    "height": 880, 
                    "url": "http://localhost:5000/v0/resolve/8cea70d75c81d59269093583752a4e08f8fbefda", 
                    "width": 880
                  }, 
                  {
                    "content_type": "image/jpeg", 
                    "height": 660, 
                    "url": "http://localhost:5000/v0/resolve/460b7a5fd4d320a2b00bfdbd535f6a65afc3cdd5", 
                    "width": 880
                  }, 
                  {
                    "content_type": "image/jpeg", 
                    "height": 1600, 
                    "url": "http://localhost:5000/v0/resolve/c6eec2fa9f7bb15d8b1df109a01cd8a000075f71", 
                    "width": 1200
                  }
                ], 
                "meta": {
                  "collection": "NPO Journalistiek", 
                  "ocd_url": "http://backstage-api.openstate.eu/v0/npo_journalistiek/journalistiek_Oben_290_40705", 
                  "original_object_id": "Oben_290_40705", 
                  "original_object_urls": {}, 
                  "processing_finished": "2015-05-26T16:19:17.874249", 
                  "processing_started": "2015-05-26T16:19:17.708490", 
                  "rights": "undefined", 
                  "source_id": "npo_journalistiek"
                }, 
                "title": "SP: Bussemaker moet stoppen met leenstelsel"
              }
            }
          ], 
          "max_score": 3.3434153, 
          "total": 11
        }, 
        "took": 2
      }


   **Query**

   Besides standard keyword searches, a basic query syntax is supported. This syntax supports the following special characters:

   - ``+`` signifies an AND operation

   - ``|`` signifies an OR operation
   - ``-`` negates a single token
   - ``"`` wraps a number of tokens to signify a phrase for searching
   - ``*`` at the end of a term signifies a prefix query
   - ``(`` and ``)`` signify precedence

   The default strategy is to perform an AND query.

   **Facets**

   The ``facets`` object determines which facets should be returned. The keys of this object should contain the names of a the requested facets, the values should be objects. These objects are used to set per facet options. Facet defaults will be used when the options dictionary is empty.

   To specify the number of facet values that should be returned (for term based facets):

   .. sourcecode:: javascript

      {
         "media_content_type": {"count": 100},
         "author": {"count": 5}
      }

   For a date based facet the 'bucket size' of the histogram can be specified:

   .. sourcecode:: javascript

      {
         "date": {"interval": "year"}
      }

   Allowed sizes are ``year``, ``quarter``, ``month``, ``week`` and ``day`` (the default size is ``month``).

   **Filters**

   Results can be filtered on one or more properties. Each key of the ``filters`` object represents a filter, the values should be objects. When filtering on multiple fields only documents that match all filters are included in the result set. The names of the filters match those of the facets.

   For example, to retrieve documents that have media associated with them of the type ``image/jpeg`` **or** ``image/png`` **and** a  ``KRO`` as one of the authors:

   .. sourcecode:: javascript

      {
         "media_content_type": {
            "terms": ['image/jpeg', 'image/png']
         },
         "author": {
            "terms": ["KRO"]
         }
      }

   Use the following format to filter on a date range:

   .. sourcecode:: javascript

      {
         "date": {
            "from": "2011-12-24",
            "to": "2011-12-28"
         }
      }

   :jsonparameter query: one or more keywords.
   :jsonparameter filters: an object with field and values to filter on (optional).
   :jsonparameter facets: an object with fields for which to return facets (optional).
   :jsonparameter sort: the field the search results are sorted on. By default, results are sorted by relevancy to the query.
   :jsonparameter size: the maximum number of documents to return (optional, defaults to 10).
   :jsonparameter from: the offset from the first result (optional, defaults to 0).
   :statuscode 200: OK, no errors.
   :statuscode 400: Bad Request. An accompanying error message will explain why the request was invalid.

.. _rest_source_search:

Searching within a single collection
------------------------------------


.. http:post:: /(source_id)/search

   Search for objects within a specific dataset. The objects returned by this method will also include fields that are specific to the queried dataset, rather than only those fields that all indexed datasets have in common.

   See specifications of the :ref:`search method <rest_search>` for the request and response format.

   :jsonparameter query: one or more keywords.
   :jsonparameter filters: an object with field and values to filter on (optional).
   :jsonparameter facets: an object with fields for which to return facets (optional).
   :jsonparameter sort: the field the search results are sorted on. By default, results are sorted by relevancy to the query.
   :jsonparameter size: the maximum number of documents to return (optional, defaults to 10).
   :jsonparameter from: the offset from the first result (optional, defaults to 0).
   :statuscode 200: OK, no errors.
   :statuscode 400: Bad Request. An accompanying error message will explain why the request was invalid.
   :statuscode 404: The requested source does not exist.

.. _rest_get:

Retrieving a single object
--------------------------

.. http:get:: /(source_id)/(object_id)

   Retrieve the contents of a single object.

   **Example request**

   .. sourcecode:: http

      $ curl -i 'http://backstage-api.openstate.eu/v0/journalistiek/Oben_290_40445'

   **Example response**

   .. sourcecode:: http

      HTTP/1.1 200 OK
      content-type: application/json
      content-length: 3167
      date: Wed, 27 May 2015 12:55:04 GMT
      
      {
        "Ancestors": [
          {
            "ItemId": 91162, 
            "ItemType": 30
          }, 
          {
            "ItemId": 3342, 
            "ItemType": 20
          }, 
          {
            "ItemId": 578, 
            "ItemType": 10
          }, 
          {
            "ItemId": 1, 
            "ItemType": 1
          }
        ], 
        "Audio": null, 
        "Body": "<p>\n\tHet moet een feestdag worden, de inhuldiging van Willem Alexander op 30 April in Amsterdam. Maar Amsterdam en het koningshuis hebben een moeizame relatie.</p>\n", 
        "Broadcasters": [
          {
            "Id": 12, 
            "Name": "AVRO"
          }, 
          {
            "Id": 13, 
            "Name": "TROS"
          }
        ], 
        "Broadcasts": null, 
        "Categories": null, 
        "Date": "2013-02-27T18:15:00", 
        "DateCreated": null, 
        "DateIndexed": "2015-05-26T06:34:29", 
        "DateOffline": null, 
        "DateOnline": null, 
        "DomainId": 1, 
        "Dossiers": [
          {
            "Id": 30, 
            "Name": "Koningshuis"
          }
        ], 
        "Id": "Oben_290_40445", 
        "Image": {
          "Id": 247337, 
          "Key": "01f358bc-8246-4ab0-93c8-ef13701c1ffc"
        }, 
        "ItemId": 40445, 
        "ItemType": 290, 
        "Keywords": null, 
        "LatestUpdateDate": "2015-05-26T06:00:22.99", 
        "ListTitle": null, 
        "Locations": null, 
        "Mid": "TROS_1331024", 
        "ProgramId": 578, 
        "ProgramImage": {
          "Id": 247145, 
          "Key": "26dc58ab-ab59-41da-89ab-bb0318f7dfdf"
        }, 
        "ProgramTitle": "EenVandaag", 
        "Summary": null, 
        "Title": "Reconstructie 'Geen woning, geen kroning'", 
        "Url": "http://www.eenvandaag.nl/seizoenen/2013/27-02-2013/reconstructie-geen-woning-geen-kroning", 
        "Video": {
          "Id": 123055, 
          "Mid": "TROS_1331024", 
          "Offline": null, 
          "Online": null, 
          "Start": 882, 
          "Stop": 1588, 
          "Stream": null, 
          "Type": 1
        }, 
        "authors": [
          "AVRO", 
          "TROS"
        ], 
        "date": "2013-02-27T18:15:00", 
        "date_granularity": 14, 
        "description": "<p>\n\tHet moet een feestdag worden, de inhuldiging van Willem Alexander op 30 April in Amsterdam. Maar Amsterdam en het koningshuis hebben een moeizame relatie.</p>\n", 
        "enrichments": {}, 
        "hidden": false, 
        "media_urls": [
          {
            "content_type": "image/jpeg", 
            "height": 563, 
            "url": "http://localhost:5000/v0/resolve/7c8ac5870b7797bfe93f6d5e9bb6553993ee4c5f", 
            "width": 1000
          }, 
          {
            "content_type": "image/jpeg", 
            "height": 880, 
            "url": "http://localhost:5000/v0/resolve/ee65549400c539f20c95e0cb3ee6bec9e43043f6", 
            "width": 880
          }, 
          {
            "content_type": "image/jpeg", 
            "height": 660, 
            "url": "http://localhost:5000/v0/resolve/13925c94b67bdc5e0398971c6676ca2d2cd98fed", 
            "width": 880
          }, 
          {
            "content_type": "image/jpeg", 
            "height": 1600, 
            "url": "http://localhost:5000/v0/resolve/ad9b5d1c088a0f3f89db3738acf274a2c44f86e0", 
            "width": 1200
          }
        ], 
        "meta": {
          "collection": "NPO Journalistiek", 
          "original_object_id": "Oben_290_40445", 
          "original_object_urls": {}, 
          "processing_finished": "2015-05-26T16:19:01.802124", 
          "processing_started": "2015-05-26T16:19:01.797626", 
          "rights": "undefined", 
          "source_id": "npo_journalistiek"
        }, 
        "prid": "TROS_1331024", 
        "title": "Reconstructie 'Geen woning, geen kroning'"
      }

   :statuscode 200: OK, no errors.
   :statuscode 404: The source and/or object does not exist.


.. http:get:: /(source_id)/(object_id)/source

   Retrieves the object's data in its original and unmodified form, as supplied by the data source. Being able to retrieve the object in it's original form can be useful for debugging purposes (i.e. when fields are missing or odd values are returned in the representation of the object).

   The value of the ``Content-Type`` response header depends on the type of data that is returned by the data provider.

   **Example request**

   .. sourcecode:: http

      $ curl -i 'http://backstage-api.openstate.eu/v0/journalistiek/Oben_290_40445/source'

   **Example response**

   .. sourcecode:: http

      HTTP/1.1 200 OK
      content-type: application/json
      content-length: 1339
      date: Wed, 27 May 2015 12:57:47 GMT
      
      {"ItemId": 40445, "DateIndexed": "2015-05-26T06:34:29", "DomainId": 1, "Title": "Reconstructie 'Geen woning, geen kroning'", "Mid": "TROS_1331024", "Broadcasts": null, "Ancestors": [{"ItemId": 91162, "ItemType": 30}, {"ItemId": 3342, "ItemType": 20}, {"ItemId": 578, "ItemType": 10}, {"ItemId": 1, "ItemType": 1}], "DateCreated": null, "Body": "<p>\n\tHet moet een feestdag worden, de inhuldiging van Willem Alexander op 30 April in Amsterdam. Maar Amsterdam en het koningshuis hebben een moeizame relatie.</p>\n", "ItemType": 290, "LatestUpdateDate": "2015-05-26T06:00:22.99", "DateOnline": null, "Date": "2013-02-27T18:15:00", "Categories": null, "ProgramTitle": "EenVandaag", "Url": "http://www.eenvandaag.nl/seizoenen/2013/27-02-2013/reconstructie-geen-woning-geen-kroning", "Summary": null, "ListTitle": null, "Dossiers": [{"Id": 30, "Name": "Koningshuis"}], "Audio": null, "Image": {"Id": 247337, "Key": "01f358bc-8246-4ab0-93c8-ef13701c1ffc"}, "Locations": null, "ProgramImage": {"Id": 247145, "Key": "26dc58ab-ab59-41da-89ab-bb0318f7dfdf"}, "ProgramId": 578, "Video": {"Stream": null, "Stop": 1588, "Mid": "TROS_1331024", "Start": 882, "Online": null, "Offline": null, "Type": 1, "Id": 123055}, "Broadcasters": [{"Id": 12, "Name": "AVRO"}, {"Id": 13, "Name": "TROS"}], "Keywords": null, "DateOffline": null, "Id": "Oben_290_40445"}

   :statuscode 200: OK, no errors.
   :statuscode 404: The requested source and/or object does not exist.

.. todo::

    - The stats functionality is currently not working

.. http:get:: /(source_id)/(object_id)/stats

   Retrieves statistics about the usage of the object within the NPO Backstage API. Currently these statistics are very basic, however, we do collect a lot more detailed information. I you wish to see additional stats here, please let us know.

   **Example request**

   .. sourcecode:: http

      $ curl -i 'http://backstage-api.openstate.eu/v0/journalistiek/Oben_290_40445/stats'

   **Example response**

   .. sourcecode:: http

      HTTP/1.1 200 OK
      content-type: application/json
      content-length: 115
      date: Wed, 27 May 2015 13:00:24 GMT
      
      {
        "n_appeared_in_search_results": 0, 
        "n_appeared_in_similar_results": 0, 
        "n_get": 0, 
        "n_get_source": 0
      }

   :statuscode 200: OK, no errors.
   :statuscode 404: The requested source and/or object does not exist.

.. _rest_similar:

Similar items
-------------

.. http:post:: /similar/(object_id)

  Retrieve objects similar to the object with id ``object_id`` across all indexed datasets (i.e. it could return items with similar descriptions). From the contents of the object, the most descriptive terms ("descriptive" here means the terms with the highest tf-idf value in the document) are used to search across the data sources.

  As a search is executed, the response format is exactly the same as the response returned by the :ref:`search endpoint <rest_search>`. The request format is almost the same, with the exception that a query can't be specified (as the document with id ``object_id`` is considered the query). That means that faceting, filtering and sorting on the resulting set are fully supported.

  **Example request**

  .. sourcecode:: http

    $ curl -i -XPOST 'http://backstage-api.openstate.eu/v0/similar/<object_id>' -d '{
       "facets": {
          "collection": {},
          "date": {"interval": "day"}
       },
       "filters": {
          "media_content_type": {"terms": ["image/jpeg"]}
       },
       "size": 10,
       "from": 30,
       "sort": "date"
    }'

  :jsonparameter filters: an object with field and values to filter on (optional).
  :jsonparameter facets: an object with fields for which to return facets (optional).
  :jsonparameter sort: the field the search results are sorted on. By default, results are sorted by relevancy to the query.
  :jsonparameter size: the maximum number of documents to return (optional, defaults to 10).
  :jsonparameter from: the offset from the first result (optional, defaults to 0).
  :statuscode 200: OK, no errors.
  :statuscode 400: Bad Request. An accompanying error message will explain why the request was invalid.


.. http:post:: /(source_id)/similar/(object_id)

  Retrieve objects similar to the object with id ``object_id`` from the dataset specified by ``source_id``. You can find similar objects in the same data source, or objects in a different data sources that are similar to the provided object.

  :jsonparameter filters: an object with field and values to filter on (optional).
  :jsonparameter facets: an object with fields for which to return facets (optional).
  :jsonparameter sort: the field the search results are sorted on. By default, results are sorted by relevancy to the query.
  :jsonparameter size: the maximum number of documents to return (optional, defaults to 10).
  :jsonparameter from: the offset from the first result (optional, defaults to 0).
  :statuscode 200: OK, no errors.
  :statuscode 400: Bad Request. An accompanying error message will explain why the request was invalid.

.. _rest_resolver:

Resolver
--------
The NPO Backstage API provides all (media) urls as NPO Backstage Resolver URLs. This will route all requests for content through the API, which will process and validate the URL, and provide a redirect to the original content source. This will allow for caching or rate limiting on API level in the future, to prevent excessive amounts of requests to the sources.

.. http:get:: /resolve/(url_hash)

  Resolves the provided URL, and redirects the request with a 302 if it is valid. If it is not, a 404 is returned. Depending on the Accept header in the request, it returns a JSON-encoded response detailing what went wrong, or a HTML-page, allowing for transparent use in websites.

    **Example json request**

    .. sourcecode:: http

      $ curl -i -Haccept:application/json -XGET http://backstage-api.openstate.eu/v0/resolve/<url_hash>

    **Example browser-like request**

    .. sourcecode:: http

      $ curl -i -Haccept:text/html -XGET http://backstage-api.openstate.eu/v0/resolve/<url_hash>

    **Example success response**

    .. sourcecode:: http

      HTTP/1.0 302 Found
      Location: http://example.com/example.jpg

    .. sourcecode:: http

      HTTP/1.0 302 FOUND
      Location: http://<STATIC_SUB_DOMAIN>.openstate.eu/media/<img_name>.jpg"

    **Example failed json response**

    .. sourcecode:: http

      HTTP/1.0 404 NOT FOUND
      Content-Type: application/json
      Content-Length: 98
      Date: Sat, 24 May 2014 14:33:00 GMT

      {
        "error": "URL is not available; the source may no longer be available",
        "status": "error"
      }

    **Example failed HTML response**

    .. sourcecode:: http

      HTTP/1.0 404 NOT FOUND
      Content-Type: text/html; charset=utf-8
      Content-Length: 123
      Date: Sat, 24 May 2014 14:32:37 GMT

      <html>
        <body>
          There is no original url available. You may have an outdated URL, or the resolve id is incorrect.
        </body>
      </html>
