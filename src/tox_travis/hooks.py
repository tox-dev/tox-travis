"""Tox hook implementations."""
import tox
from .utils import parser_cfg, config_cfg
from .toxenv import default_toxenv, override_ignore_outcome
from .after import travis_after_monkeypatch


@tox.hookimpl(trylast=True)
def tox_addoption(parser):
    """Add arguments and override TOXENV."""
    parser.add_argument(
        '--travis-after', dest='travis_after', action='store_true',
        help='Exit successfully after all Travis jobs complete successfully.')

    cfg = parser_cfg(parser)
    if cfg:
        default_toxenv(cfg)


@tox.hookimpl
def tox_configure(config):
    """Check for the presence of the added options."""
    cfg = config_cfg(config)

    if config.option.travis_after:
        travis_after_monkeypatch(cfg)

    override_ignore_outcome(config, cfg)
