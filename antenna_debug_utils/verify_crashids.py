# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Verifies crash ids exist in s3 bucket

Given a list of crashids, this script goes through the list and verifies
they are all in the bucket.

Requires:

* Python 3.5
* gevent
* boto3

Usage::

    python3 verify_crashids.py [FILENAME]


.. NOTE::

   You have to edit the script and fill in the BUCKET and REGION values.

   FIXME(willkg): We should change that to be params.

"""

from gevent import monkey; monkey.patch_all()  # noqa

from collections import deque
import sys

import boto3
from botocore.client import Config
import gevent


BUCKET = ''
REGION = ''
ACCESS_KEY_ID = ''
SECRET_ACCESS_KEY = ''


def get_conn():
    session = boto3.session.Session()

    kwargs = {
        'service_name': 's3',
        'region_name': REGION,
        'config': Config(s3={'addressing_style': 'path'})
    }

    if ACCESS_KEY_ID and SECRET_ACCESS_KEY:
        kwargs['aws_access_key_id'] = ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = SECRET_ACCESS_KEY

    return session.client(**kwargs)


def get_date_from_crash_id(crash_id):
    return '20' + crash_id[-6:]


def crashid_to_key(crashid):
    return 'v2/raw_crash/{entropy}/{date}/{crash_id}'.format(
        entropy=crashid[:3],
        date=get_date_from_crash_id(crashid),
        crash_id=crashid,
    )


CRASHES = deque()
RESULTS = []
PER_SEC = 0


def worker(id_, conn):
    global PER_SEC

    total = successes = 0
    failed = []

    while CRASHES:
        crashid = CRASHES.pop()

        total += 1
        PER_SEC += 1

        try:
            key = crashid_to_key(crashid)
            conn.head_object(
                Bucket=BUCKET,
                Key=key,
            )
            successes += 1
        except Exception as exc:
            print('FAIL: %s %s' % (crashid, exc))
            failed.append((crashid, exc))

    RESULTS.append((total, successes, failed))


def main(args):
    global PER_SEC

    fn = args[0]

    conn = get_conn()

    with open(fn, 'r') as fp:
        for crashid in fp:
            CRASHES.append(crashid.strip())

    workers = [gevent.spawn(worker, i, conn) for i in range(10)]
    total = 0

    while CRASHES:
        total += PER_SEC
        print('%d %d/s' % (total, PER_SEC))
        PER_SEC = 0
        gevent.sleep(1)

    gevent.sleep(5)

    total = successes = 0
    failed = []

    for res in RESULTS:
        total += res[0]
        successes += res[1]
        failed.extend(res[2])

    print('Total lines: %d' % total)
    print('  Success: %d' % successes)
    print('  Fails:   %d' % len(failed))
    for fail in failed:
        print(fail)


def cli_main():
    # FIXME(willkg): Fix argument parsing here
    sys.exit(main(sys.argv[1:]))


if __name__ == '__main__':
    cli_main()
