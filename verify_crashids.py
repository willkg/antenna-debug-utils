import sys

import boto3
from botocore.client import ClientError, Config


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


def main(args):
    fn = args[0]

    conn = get_conn()

    lines = 0
    failed = []

    with open(fn, 'r') as fp:
        for crashid in fp:
            crashid = crashid.strip()

            try:
                conn.head_object(
                    Bucket=BUCKET,
                    Key=crashid_to_key(crashid)
                )
                lines += 1

            except Exception as exc:
                print('FAIL: %s: %s' % (crashid, exc))
                failed.append(crashid)

    print('Total crashes checked: %d' % lines)
    print('Total fails: %d' % len(failed))
    for fail in failed:
        print(fail)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
