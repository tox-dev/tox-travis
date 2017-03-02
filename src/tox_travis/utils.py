"""Shared constants and utility functions."""
import sys
import os
import py

# Mapping Travis factors to the associated env variables
TRAVIS_FACTORS = {
    'os': 'TRAVIS_OS_NAME',
    'language': 'TRAVIS_LANGUAGE',
    'python': 'TRAVIS_PYTHON_VERSION',
}


def parse_dict(value):
    """Parse a dict value from the tox config.

    .. code-block: ini

        [travis]
        python =
            2.7: py27, docs
            3.5: py{35,36}

    With this config, the value of ``python`` would be parsed
    by this function, and would return::

        {
            '2.7': 'py27, docs',
            '3.5': 'py{35,36}',
        }

    """
    lines = [line.strip() for line in value.strip().splitlines()]
    pairs = [line.split(':', 1) for line in lines if line]
    return dict((k.strip(), v.strip()) for k, v in pairs)


def parser_cfg(parser):
    """Get an IniConfig from the parser.

    Use the same method to parse the arguments that Tox does.
    Needs to have all of the options added, or else the
    parsing may not work in some cases. Even when adding
    ``trylast=True`` to the hook implementation, that may
    still happen if other used plugins run first.

    Figure out the configfile that Tox is going to use, and
    create a ``py.iniconfig.IniConfig`` from that file, or
    ``None`` if no configuration file could be found.
    """
    try:
        option = parser._parse_args(sys.argv[1:])
    except:
        option = None

    # File finding algorithm copied from Tox
    # Except for the default basename.
    basename = option.configfile if option else 'tox.ini'
    if os.path.isabs(basename):
        inipath = py.path.local(basename)
    else:
        for path in py.path.local().parts(reverse=True):
            inipath = path.join(basename)
            if inipath.check():
                break
        else:
            inipath = py.path.local().join('setup.cfg')
            if not inipath.check():
                return  # We couldn't find a config

    return py.iniconfig.IniConfig(inipath)


def config_cfg(config):
    """Get the IniConfig from the Tox config.

    The Tox config is it's own wrapper around ``IniConfig`` from
    ``py``. Get the underlying ``IniConfig`` from the config.
    """
    return config._cfg
