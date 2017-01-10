"""Tox hook implementations."""
import os
import py
import tox
import tox.config
from .toxenv import default_toxenv
from .after import travis_after_monkeypatch


@tox.hookimpl
def tox_addoption(parser):
    """Add arguments and override TOXENV."""
    parser.add_argument(
        '--travis-after', dest='travis_after', action='store_true',
        help='Exit successfully after all Travis jobs complete successfully.')

    default_toxenv()


@tox.hookimpl
def tox_configure(config):
    """Check for the presence of the added options."""

    if 'TRAVIS' not in os.environ:
        return

    if config.option.travis_after:
        travis_after_monkeypatch()

    # When `obey_outcomes` is set to `False`, this will pass the return code from tox to travis
    # regardless of how `ignore_outcome` was configured.
    tox_config = py.iniconfig.IniConfig('tox.ini')
    travis_reader = tox.config.SectionReader("travis", tox_config)
    if not travis_reader.getbool('obey_outcomes', True):
        for env in config.envlist:
            config.envconfigs[env].ignore_outcome = False
