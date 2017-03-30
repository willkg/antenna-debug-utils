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


def run_program(progname, config_class, args, parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(prog=progname)

    parser.add_argument(
        '--config',
        help=(
            'Config file in ENV format. Setting options on the command line '
            'will override values in the config file.'
        ),
    )

    options = config_class.get_required_config()

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
        else:
            kwargs['default'] = NO_VALUE

        parser.add_argument('--%s' % opt.key.lower(), **kwargs)

    parser.set_defaults(handler=config_class)

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
    comp_config = config.with_options(config_class)
    for opt in options:
        val = getattr(vals, opt.key.lower(), NO_VALUE)
        if val is NO_VALUE:
            if opt.default is NO_VALUE:
                missing_opts.append(opt.key.lower())

        else:
            try:
                val = comp_config(opt.key.lower())
            except ConfigurationMissingError as cme:
                missing_opts.append(opt.key.lower())
            except Exception as exc:
                parse_errors.append(
                    (opt.key.lower(), str(exc))
                )

    if missing_opts:
        parser.print_usage(sys.stderr)
        parser._print_message(
            (
                'the following are required: %s\n' %
                ', '.join([opt for opt in missing_opts])
            ),
            sys.stderr
        )
        return 2

    if parse_errors:
        parser.print_usage(sys.stderr)
        parser._print_message('the following have value errors:\n', sys.stderr)
        for opt, msg in parse_errors:
            parser._print_message('%s:\n%s\n' % (opt, indent(msg)), sys.stderr)
        return 2

    return vals.handler(config).invoke()
