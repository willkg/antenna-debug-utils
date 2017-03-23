from gevent import monkey; monkey.patch_all()  # noqa

import gevent
from queue import Queue
import sys

import boto3
from botocore.client import Config


BUCKET=''
REGION=''


def get_conn():
    session = boto3.session.Session()

    return session.client(
        service_name='s3',
        region_name=REGION,
        config=Config(s3={'addressing_style': 'path'})
    )


def get_date_from_crash_id(crash_id):
    return '20' + crash_id[-6:]


def crashid_to_key(crashid):
    return 'v2/raw_crash/{entropy}/{date}/{crash_id}'.format(
        entropy=crashid[:3],
        date=get_date_from_crash_id(crashid),
        crash_id=crashid,
    )


CRASHES = Queue()
RESULTS = []


def worker(conn):
    total = successes = 0
    failed = []

    while True:
        if not CRASHES:
            break

        crashid = CRASHES.get()

        total += 1

        try:
            conn.head_object(
                Bucket=BUCKET,
                Key=crashid_to_key(crashid)
            )
            successes += 1
        except Exception as exc:
            failed.append((crashid, exc))
        CRASHES.task_done()

    RESULTS.append((total, successes, failed))


def main(args):
    fn = args[0]

    conn = get_conn()

    with open(fn, 'r') as fp:
        for crashid in fp:
            CRASHES.put(crashid)

    workers = [gevent.spawn(worker, conn) for i in range(10)]

    gevent.joinall(workers)

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


if __name__ == '__main__':
    gevent.monkey
    sys.exit(main(sys.argv[1:]))
