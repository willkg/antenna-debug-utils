# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Log parser for Antenna logs

This analyzes what happened in some period of time and spits out stats.

"""

import argparse
from collections import namedtuple
import gzip
import sys


GZIP_HEADER = b'\037\213'

CRASH_ID_LENGTH = 36

RECEIVE = 'receive'
SAVE = 'save'


CrashEvent = namedtuple('CrashEvent', ['timestamp', 'host', 'crashid', 'action'])


class HostInfo:
    def __init__(self, host, pid, start, stop=None, crashes_in=None, crashes_out=None):
        self.host = host
        self.pid = pid
        self.start = start
        self.stop = stop
        self.crashes_in = crashes_in or []
        self.crashes_out = crashes_out or []


def get_bounded_token(line, bound):
    """Slurps the next token bounded by some boundary character"""
    index = line.find(bound)
    token = line[0:index]
    return token, line[index + len(bound):]


def get_bracket_token(line):
    """Slurps the next token enclosed in [ ]"""
    token, line = get_bounded_token(line, '] ')
    return token.strip()[1:], line


def parse_line(line):
    """Parses a line from the log"""
    # FIXME(willkg): This tokenizing is gross

    timestamp = host = crashid = action = None

    if not line.startswith('['):
        return None

    # Timestamp
    timestamp, line = get_bracket_token(line)

    # ANTENNA and host
    host, line = get_bracket_token(line)
    host = host.replace('ANTENNA ', '')

    # log level (throw away)
    _, line = get_bracket_token(line)

    # source (throw away)
    _, line = get_bounded_token(line, ' ')

    # crashid
    possible_crashid, line = get_bounded_token(line, ' ')
    possible_crashid = possible_crashid.rstrip(':')
    if len(possible_crashid) == CRASH_ID_LENGTH:
        crashid = possible_crashid

    # action
    action = SAVE if line.strip().startswith('saved') else RECEIVE

    data = CrashEvent(timestamp, host, crashid, action)
    return data


def parse_files(start_date, end_date, filenames):
    """Parses a file looking at records between bounded dates

    :arg str start_date: the start date as "YYYY-mm-dd HH:MM:SS"
    :arg str end_date: the end date as "YYYY-mm-dd HH:MM:SS"
    :arg list filenames: the list of files to look at

    :returns: ``(hostinfo_map, crashes_in, crashes_out)``

    """
    filenames = set(filenames)

    lines = 0
    lines_beyond_end_date = 0

    # Map of "host pid" -> Hostinfo
    hostinfo_map = {}

    # Map of crashid -> CrashEvent
    crashes_in = {}
    crashes_out = {}

    for filename in filenames:
        with open(filename, 'rb') as fp:
            possible_header = fp.read(2)

        if possible_header == GZIP_HEADER:
            opener = gzip.open
        else:
            opener = open

        with opener(filename, 'r') as fp:
            for line in fp:
                if not isinstance(line, str):
                    line = line.decode('utf-8')

                if not line.startswith('[') or '[ANTENNA' not in line:
                    continue

                timestamp = line[1:20]
                if timestamp < start_date:
                    continue

                if timestamp > end_date:
                    lines_beyond_end_date += 1
                    if lines_beyond_end_date > 5000:
                        break

                data = parse_line(line.strip())
                if not data or not data.crashid:
                    continue

                lines += 1

                if data.host not in hostinfo_map:
                    host, pid = data.host.split(' ')
                    hostinfo_map[data.host] = HostInfo(host, pid, start=data.timestamp)

                hostinfo = hostinfo_map[data.host]
                hostinfo.stop = data.timestamp

                # Only count receives before the end date
                if data.action == RECEIVE and data.timestamp < end_date:
                    crashes_in[data.crashid] = data
                    hostinfo.crashes_in.append(data.crashid)

                elif data.action == SAVE:
                    if data.timestamp < end_date or data.crashid in crashes_in:
                        crashes_out[data.crashid] = data
                        hostinfo.crashes_out.append(data.crashid)

    print('lines: %d' % lines)
    return hostinfo_map, crashes_in, crashes_out


def main(args):
    parser = argparse.ArgumentParser(
        description='Antenna log parser',
        epilog='For more information, see https://github.com/willkg/antenna-log-parser'
    )
    parser.add_argument('start', help='start date/time--substring of YYYY-MM-DD HH:MM')
    parser.add_argument('end', help='end date/time--substring of YYYY-MM-DD HH:MM')
    parser.add_argument('filename', help='log files', nargs='*')

    args = parser.parse_args()

    hostinfo_map, crashes_in, crashes_out = parse_files(args.start, args.end, args.filename)

    print('From %s to %s' % (args.start, args.end))
    print()
    print('total crashes in:  %d' % len(crashes_in))
    print('total crashes out: %d' % len(crashes_out))
    print('delta:             %d' % (len(crashes_in) - len(crashes_out)))
    print('percent success:   %2.5f' % (100.0 - (len(crashes_out) / len(crashes_in))))
    print()

    print('Hosts (%d):' % len(hostinfo_map))
    print()

    fine_hosts = [
        hostinfo for host, hostinfo in hostinfo_map.items()
        if len(hostinfo.crashes_in) == len(hostinfo.crashes_out)
    ]
    print('Hosts that did fine (%d):' % len(fine_hosts))
    for hostinfo in sorted(fine_hosts, key=lambda x: (x.host, int(x.pid))):
        print('   %-68s  %3s  %26s  %26s  %6s  %6s' % (
            hostinfo.host,
            hostinfo.pid,
            hostinfo.start,
            hostinfo.stop,
            len(hostinfo.crashes_in),
            len(hostinfo.crashes_out)
        ))
    print()

    troubled_hosts = [
        hostinfo for host, hostinfo in hostinfo_map.items()
        if len(hostinfo.crashes_in) != len(hostinfo.crashes_out)
    ]
    print('Hosts that had trouble (%d):' % len(troubled_hosts))
    for hostinfo in sorted(troubled_hosts, key=lambda x: x.start):
        print('   %-68s  %3s  %26s  %26s  %6s  %6s' % (
            hostinfo.host,
            hostinfo.pid,
            hostinfo.start,
            hostinfo.stop,
            len(hostinfo.crashes_in),
            len(hostinfo.crashes_out)
        ))
    print()

    in_set = set(crashes_in.keys())
    out_set = set(crashes_out.keys())

    print('Received but not saved (%d):' % len((in_set - out_set)))
    for crashid in sorted(in_set - out_set, key=lambda x: crashes_in[x].timestamp):
        print('   %s  %-70s  %s' % (
            crashes_in[crashid].timestamp,
            crashes_in[crashid].host,
            crashes_in[crashid].crashid,
        ))

    print('Saved but not received (%d):' % len((out_set - in_set)))
    for crashid in sorted(out_set - in_set, key=lambda x: crashes_out[x].timestamp):
        print('   %s  %-70s  %s' % (
            crashes_out[crashid].timestamp,
            crashes_out[crashid].host,
            crashes_out[crashid].crashid,
        ))


def cli_main():
    # FIXME(willkg): Fix argument parsing here
    sys.exit(main(sys.argv[1:]))


if __name__ == '__main__':
    cli_main()
