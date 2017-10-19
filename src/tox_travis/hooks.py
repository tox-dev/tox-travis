"""Tox hook implementations."""
import os
import tox
from .toxenv import (
    default_toxenv,
    override_ignore_outcome,
)
from .hacks import pypy_version_monkeypatch
from .after import travis_after_monkeypatch


@tox.hookimpl
def tox_addoption(parser):
    """Add arguments and override TOXENV."""
    parser.add_argument(
        '--travis-after', dest='travis_after', action='store_true',
        help='Exit successfully after all Travis jobs complete successfully.')

    if 'TRAVIS' in os.environ:
        default_toxenv()
        pypy_version_monkeypatch()


@tox.hookimpl
def tox_configure(config):
    """Check for the presence of the added options."""
    if 'TRAVIS' in os.environ:
        if config.option.travis_after:
            travis_after_monkeypatch()
        override_ignore_outcome(config)
