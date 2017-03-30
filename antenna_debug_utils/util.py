import argparse
import sys

from everett import NO_VALUE, ConfigurationMissingError
from everett.manager import ConfigManager, ConfigObjEnv, ConfigEnvFileEnv


def handle_no_value(parser):
    def _handle_no_value(val):
        if val is NO_VALUE:
            return NO_VALUE
        return parser(val)
    return _handle_no_value


def indent(msg, prefix='    '):
    return '\n'.join(
        [prefix + part for part in msg.splitlines()]
    )


def print_error(msg):
    sys.stderr.write(msg)


def run_program(app, args, parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(prog=app.program_name)

    parser.add_argument(
        '--config',
        help=(
            'Config file in ENV format. Setting options on the command line '
            'will override values in the config file.'
        ),
    )

    options = app.get_required_config()

    for opt in options:
        # We don't enforce required here--we do that in a later pass so we can
        # take configuration files into account.
        kwargs = {
            'help': opt.doc,
            'type': handle_no_value(opt.parser),
            'action': 'store',
        }

        if opt.default is not NO_VALUE:
            kwargs['default'] = opt.default
            kwargs['help'] += ' Default is %s.' % opt.default

        parser.add_argument('--%s' % opt.key.lower(), **kwargs)

    parser.set_defaults(handler=app)

    # Parse the args--this will exit if there's a --help
    vals, extra = parser.parse_known_args(args)

    config = ConfigManager([
        ConfigObjEnv(vals),

        # FIXME(willkg): It'd be better if this was an INI file.
        ConfigEnvFileEnv(vals.config),
    ])

    # Now go through and make sure all the required options were supplied.
    missing_opts = []
    parse_errors = []
    comp_config = config.with_options(app)
    for opt in options:
        try:
            comp_config(opt.key.lower())
        except ConfigurationMissingError as cme:
            missing_opts.append(opt.key.lower())
        except Exception as exc:
            parse_errors.append(
                (opt.key.lower(), str(exc))
            )

    if missing_opts:
        parser.print_usage(sys.stderr)
        print_error(
            'the following are required: %s\n' %
            ', '.join([opt for opt in missing_opts])
        )
        return 2

    if parse_errors:
        parser.print_usage(sys.stderr)
        print_error('the following have value errors:\n')
        for opt, msg in parse_errors:
            print_error('%s:\n%s\n' % (opt, indent(msg)))
        return 2

    return vals.handler(config).invoke()
