"""Tox hook implementations."""
import tox
from .toxenv import default_toxenv
from .after import travis_after


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
    if config.option.travis_after:
        travis_after()
