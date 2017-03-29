==================
Antenna log parser
==================

This is a log parser for `Antenna <https://github.com/mozilla/antenna>`_ logs. I
wrote it very quickly to help me figure out how load tests were going.

:License: MPLv2
:Author: Will Kahn-Greene


Install
=======

1. Clone the repo::

       git clone https://github.com/willkg/antenna-debug-utils

2. If you have `pipsi <https://pypi.python.org/pypi/pipsi>`_, you can then do::

       cd antenna-debug-utils
       pipsi install -e .


   If you do not have pipsi or don't want to use it, you can do::

       cd antenna-debug-utils

       # create a python3 virtualenv

       # activate your virtualenv

       python setup.py -e .


Quickstart for log parser
=========================

Usage::

    log_parser <START> <END> <FILENAME> [<FILENAME> ...]


Arguments:

**START** and **END**

    This is the start and end date/time. The log parser is doing string
    comparisons on the datestamp at the beginning of each line, so you can
    specify the date or the date and time in any substring combination.

    For example, if you want to look at everything on 2017-03-20, you'd do::

        python log_parser.py 2017-03-20 2017-03-21 <FILENAME>


**FILENAME**

    The log file you want to parse.

    This handles .gz files.


Quickstart for verify crashids
==============================

FIXME(willkg): Write this


Quickstart for faux processor
=============================

FIXME(willkg): Write this
