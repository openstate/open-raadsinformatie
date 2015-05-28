.. _quickstart:

Quickstart
===================

Anxious to get started right away? This page provides you with a short introduction on how to get started with querying the NPO Backstage API.

The base URL of the API is :rest_api_v0:`v0`, but it won't return any data.

.. warning::
   The URL of the API is currently http://backstage-api.openstate.eu, but will most likely change soon.

To see which sources there are and how many items they contain, simply open the following link in your browser:

    http://backstage-api.openstate.eu/v0/sources

To retrieve some data from the API, let's retrieve 5 items with a simple search query for the word 'leenstelsel' using curl::

    curl -i -XPOST 'http://backstage-api.openstate.eu/v0/search' -d '{"query": "leenstelsel", "size": 5}'

(Note that the HTTP method used for search is 'POST' (so make sure that you're not using 'GET').)

The previous command search the whole API. You can also search through just the combined index::

    curl -i -XPOST 'http://backstage-api.openstate.eu/v0/combined_index/search' -d '{"query": "leenstelsel", "size": 5}'

Or, search only in a specific index::

    curl -i -XPOST 'http://backstage-api.openstate.eu/v0/journalistiek/search' -d '{"query": "leenstelsel", "size": 5}'
