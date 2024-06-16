Welcome to ParaMPL's documentation!
===================================

ParaMPL allows writing of justified paragraphs to matplotlib plots.
Possibly values are 'full', 'center', 'left', 'right'.

For each word, it first writes it invisibly to calculate its length. Then, the paragraph is split in lines of
appropriate length and justified as requested.
The computed length is always kept in cache and will be sorted by font's size and style.

An example run in quickstart.py produces:

.. image:: ../sample_full.png


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   API reference <source/api>




