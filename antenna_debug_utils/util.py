import argparse

from everett import NO_VALUE
from everett.manager import ConfigManager, ConfigObjEnv, ConfigEnvFileEnv


def run_program(progname, config_class, args):
    parser = argparse.ArgumentParser(prog=progname)

    # FIXME(willkg): Add support for setting things in a config file.
    # parser.add_argument(
    #     '--config',
    #     help='Config file in ENV format',
    # )

    options = config_class.get_required_config()

    for opt in options:
        kwargs = {
            'help': opt.doc,
            'type': opt.parser,
            'action': 'store',
        }

        if opt.default is not NO_VALUE:
            kwargs['default'] = opt.default
            kwargs['help'] += ' Default is %s.' % opt.default
        else:
            kwargs['required'] = True

        parser.add_argument('--%s' % opt.key.lower(), **kwargs)

    parser.set_defaults(handler=config_class)

    # Parse the args--this will exit if there's a --help
    vals = parser.parse_known_args(args)[0]

    config = ConfigManager([
        ConfigObjEnv(vals),
        # FIXME(willkg): Add support for setting things in a config file.
        # ConfigEnvFileEnv(vals.config),
    ])

    obj = vals.handler(config)
    return obj.invoke()
