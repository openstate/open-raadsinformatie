.. _datasets:

Datasets
========

.. todo::

    - This page is not complete yet. It should be finished by the end of this week (2015-05-29).

This page gives an overview of the available data sources. For each data source it is shown which fields were used for the combined index and a description of the data source's fields.

NPO Journalistiek
------------------------

This dataset contains (meta)data from the `NPO Journalistiek portal <http://journalistiek.npo.nl/>`__. The items can be either an episode (aflevering), fragment (part of an episode), web-only content or a text article.

Combined index
^^^^^^^^^^^^^^

+------------------------+--------------------------------------+----------------------------------------+
| Combined index field   | Source field(s)                      | Comment                                |
+========================+======================================+========================================+
| ``title``              | ``Title``                            |                                        |
+------------------------+--------------------------------------+----------------------------------------+
| ``description``        | ``Body``                             |                                        |
+------------------------+--------------------------------------+----------------------------------------+
| ``prid``               | ``Mid``                              |                                        |
+------------------------+--------------------------------------+----------------------------------------+
| ``date``               | ``Date``                             |                                        |
+------------------------+--------------------------------------+----------------------------------------+
| ``authors``            | ``Broadcasters``                     |                                        |
+------------------------+--------------------------------------+----------------------------------------+
| ``media_urls``         | ``Image``                            | All images are available in 4 sizes:   |
|                        |                                      | 1000x563, 880x880, 880x660, 1200x1600  |
+------------------------+--------------------------------------+----------------------------------------+

NPO Journalistiek index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


PRID
-----------------------

PRIDs are the unique IDs given to audio and video content. This data source contains basic information for each PRID.

Combined index
^^^^^^^^^^^^^^


PRID index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


metadata
--------------------------

This index contains metadata for each PRID.

Combined index
^^^^^^^^^^^^^^

metadata index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TT888
-----------------------

This index contains the subtitles for each PRID, if available. The term TT888 stems from Teletekst page 888 which offers the subtitle overlay on TV.

Combined index
^^^^^^^^^^^^^^


TT888 index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
