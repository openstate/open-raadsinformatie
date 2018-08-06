.. _quickstart:

Quickstart
===================

Anxious to get started right away? This page provides you with a short introduction on how to get started with querying the Open Raadsinformatie and Open Stateninformatie API.

The base URL of the API is :rest_api_v0:`v0`, but it won't return any data.

.. attention::

   We refer to `api.openraadsinformatie.nl` in the examples below, but you can also use `api.openstateninformatie.nl`.

To see which sources there are and how many items they contain, simply open the following link in your browser:

    :rest_api_v0:`v0/sources`

To retrieve some data from the API, let's retrieve 5 items with a simple search query for the word 'vergadering' using curl::

    curl -i -XPOST 'http://api.openraadsinformatie.nl/v0/search' -d '{"query": "vergadering", "size": 5}'

(Note that the HTTP method used for search is 'POST' (but you can also use 'GET').)

The previous command search the whole API. You can also search through just the combined index::

    curl -i -XPOST 'http://api.openraadsinformatie.nl/v0/combined_index/search' -d '{"query": "vergadering", "size": 5}'

Or, search only in a specific index::

    curl -i -XPOST 'http://api.openraadsinformatie.nl/v0/amstelveen/search' -d '{"query": "vergadering", "size": 5}'

Or, even only specified types of documents (persons, organizations or events)::

    curl -i -XPOST 'http://api.openraadsinformatie.nl/v0/amstelveen/events/search' -d '{"query": "vergadering", "size": 5}'
