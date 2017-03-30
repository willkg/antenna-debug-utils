# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Fake processor that consumes from rmq and checks s3

This consumes crashids from a rabbitmq queue and for each crashid, verifies
that it is on s3.

Requires:

* Python 3
* boto3
* pika

To run, set a ton of stuff in the environment:

* FAUX_USER
* FAUX_PASSWORD
* FAUX_HOST
* FAUX_PORT
* FAUX_VIRTUAL_HOST
* FAUX_QUEUE
* FAUX_S3_REGION
* FAUX_S3_BUCKET

Then do:

    python3 faux_processor.py

It'll check the queue every second and pull stuff.

"""

import logging
import os
import socket
import sys
import time

import boto3
from botocore.client import Config
from everett.component import ConfigOptions, RequiredConfigMixin
import pika

from antenna_debug_utils.util import run_program


PIKA_EXCEPTIONS = (
    pika.exceptions.AMQPConnectionError,
    pika.exceptions.ChannelClosed,
    pika.exceptions.ConnectionClosed,
    pika.exceptions.NoFreeChannels,
    socket.timeout
)

# These values match Antenna throttling return values
ACCEPT = '0'
DEFER = '1'

logging.basicConfig()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_from_env(key):
    return os.environ['FAUX_%s' % key]


def get_throttle_result(crash_id):
    return crash_id[-7]


def build_pika_connection(host, port, virtual_host, user, password):
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            connection_attempts=10,
            socket_timeout=10,
            retry_delay=1,
            credentials=pika.credentials.PlainCredentials(
                user,
                password
            )
        )
    )


def get_conn(region):
    session = boto3.session.Session()

    return session.client(
        service_name='s3',
        region_name=region,
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


def check_for_crashes(channel, queue, conn, bucket):
    while True:
        # Pull a crash id from the queue
        try:
            crashid = channel.basic_get(queue=queue)
            logging.info('%s pulled from rabbitmq queue', crashid)

        except Exception as exc:
            logging.error('Failed to get crashid from queue: %s', exc)
            return

        # Verify it on s3
        try:
            key = crashid_to_key(crashid)
            conn.head_object(
                Bucket=bucket,
                Key=key
            )
            logging.info('%s exists on s3--success!', crashid)
        except Exception as exc:
            logging.error('Failed to HEAD crash: %s %s', crashid, exc)


class ProcessorProgram(RequiredConfigMixin):
    program_name = 'faux-processor'

    required_config = ConfigOptions()
    required_config.add_option(
        'host',
        doc='RabbitMQ host to connect to.'
    )
    required_config.add_option(
        'port',
        parser=int,
        doc='Port for the RabbitMQ host to connect to.'
    )
    required_config.add_option(
        'virtual_host',
        doc='Virtual host for RabbitMQ.'
    )
    required_config.add_option(
        'user',
        doc='RabbitMQ user to use.'
    )
    required_config.add_option(
        'password',
        doc='RabbitMQ password to use.'
    )
    required_config.add_option(
        'queue',
        doc='RabbitMQ queue to use.'
    )

    required_config.add_option(
        's3_region',
        default='us-west-1',
        doc='S3 region of the S3 bucket.'
    )
    required_config.add_option(
        's3_bucket',
        doc='S3 bucket to check for crashes.'
    )

    def __init__(self, config):
        self.config = config.with_options(self)

    def invoke(self):
        rmq = build_pika_connection(
            host=self.config('host'),
            port=self.config('port'),
            virtual_host=self.config('virtual_host'),
            user=self.config('user'),
            password=self.config('password'),
        )

        queue = self.config('queue')
        channel = rmq.channel()
        channel.queue_declare(queue=queue)

        bucket = self.config('s3_bucket')
        conn = get_conn()

        logging.info('Entering loop. Ctrl-C at any time to break out.')
        while True:
            check_for_crashes(channel, queue, conn, bucket)
            time.sleep(1)


def main(args):
    sys.exit(run_program(ProcessorProgram, args))


def cli_main():
    # FIXME(willkg): Fix argument parsing here
    sys.exit(main(sys.argv[1:]))


if __name__ == '__main__':
    cli_main()
