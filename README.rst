==================
Antenna log parser
==================

This is a log parser for `Antenna <https://github.com/mozilla/antenna>`_ logs. I
wrote it very quickly to help me figure out how load tests were going.

:License: MPLv2
:Author: Will Kahn-Greene


Quickstart
==========

This uses Python 2.7 without any additional dependencies.

1. Clone the repo::

       git clone https://github.com/willkg/antenna-log-parser

2. Run it::

       python log_parser.py <START> <END> <FILENAME>


Arguments:

**START** and **END**

    This is the start and end date/time. The log parser is doing string
    comparisons on the datestamp at the beginning of each line, so you can
    specify the date or the date and time in any substring combination.

    For example, if you want to look at everything on 2017-03-20, you'd do::

        python log_parser.py 2017-03-20 2017-03-21 <FILENAME>


**FILENAME**

    The log file you want to parse.
