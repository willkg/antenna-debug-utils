==================
Antenna log parser
==================

This is a log parser for `Antenna <https://github.com/mozilla/antenna>`_ logs. I
wrote it very quickly to help me figure out how load tests were going.

:License: MPLv2
:Author: Will Kahn-Greene


Install
=======

Requirements:

* Python 3
* Either pipsi or some kind of virtual environment creation thingy


Steps:

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


.. Note::

   These utilities are all pretty much in the vein of "write once, use once,
   throwaway". They might work for you. They might have bugs.

   Figured I'd collect them in case they were handy again some day.



Quickstart for log parser
=========================

This looks at a period of time in log files on the grephost and then looks
at incoming crashes vs. crashes saved, then tells you what happened and
how many might have gotten lost and which hosts were involved and so on.

For help::

    log-parser --help


Example runs::

    log-parser "2017-03-29 17:30" "2017-03-30 00:20" *.gz *.log


This can handle text files and `.gz` files.


Quickstart for faux processor
=============================

This will listen to a specified RabbitMQ queue on a specified RabbitMQ host
and every crashid it sees, it'll check to see if that crashid exists in the
specified S3 bucket.

.. Note::

   It consumes crashids from the queue.


For help::

    faux-processor --help


You can provide all the arguments on the command line or alternately
via an ENV file which you specify using the ``-config`` option.


Quickstart for verify crashids
==============================

FIXME(willkg): Write this
