import os
import sys
import re
import py
import tox

from tox.config import _split_env as split_env
try:
    from tox.config import default_factors
except ImportError:
    default_factors = None


@tox.hookimpl
def tox_addoption(parser):
    if 'TRAVIS' not in os.environ:
        return

    config = py.iniconfig.IniConfig('tox.ini')

    # Find the envs that tox knows about
    declared_envs = get_declared_envs(config)

    # Find the requested envs
    version = os.environ.get('TRAVIS_PYTHON_VERSION')
    desired_envs = get_desired_envs(config, version)

    matched = match_envs(declared_envs, desired_envs)
    os.environ.setdefault('TOXENV', ','.join(matched))

    # Travis virtualenv do not provide `pypy3`, which tox tries to execute.
    # This doesnt affect Travis python version `pypy3`, as the pyenv pypy3
    # is in the PATH.
    # https://github.com/travis-ci/travis-ci/issues/6304
    # Force use of the virtualenv `python`.
    if version and default_factors and version.startswith('pypy3.3-5.2-'):
        default_factors['pypy3'] = 'python'


def get_declared_envs(config):
    """Get the full list of envs from the tox config.

    This notably also includes envs that aren't in the envlist,
    but are declared by having their own testenv:envname section.

    The envs are expected in a particular order. First the ones
    declared in the envlist, then the other testenvs in order.
    """
    tox_section = config.sections.get('tox', {})
    envlist = split_env(tox_section.get('envlist', []))

    # Add additional envs that are declared as sections in the config
    section_envs = [
        section[8:] for section in sorted(config.sections, key=config.lineof)
        if section.startswith('testenv:')
    ]

    return envlist + [env for env in section_envs if env not in envlist]


def get_version_info():
    """Get version info from the sys module.

    Override from environment for testing.
    """
    overrides = os.environ.get('__TOX_TRAVIS_SYS_VERSION')
    if overrides:
        version, major, minor = overrides.split(',')[:3]
        major, minor = int(major), int(minor)
    else:
        version, (major, minor) = sys.version, sys.version_info[:2]
    return version, major, minor


def guess_python_env():
    """Guess the default python env to use."""
    version, major, minor = get_version_info()
    if 'PyPy' in version:
        return 'pypy3' if major == 3 else 'pypy'
    return 'py{major}{minor}'.format(major=major, minor=minor)


def get_default_envlist(version):
    """Parse a default tox env based on the version.

    The version comes from the ``TRAVIS_PYTHON_VERSION`` environment
    variable. If that isn't set or is invalid, then use
    sys.version_info to come up with a reasonable default.
    """
    if version in ['pypy', 'pypy3']:
        return version

    # Assume single digit major and minor versions
    match = re.match(r'^(\d)\.(\d)(?:\.\d+)?$', version or '')
    if match:
        major, minor = match.groups()
        return 'py{major}{minor}'.format(major=major, minor=minor)

    return guess_python_env()


def get_desired_envs(config, version):
    """Get the expanded list of desired envs."""
    travis_section = config.sections.get('tox:travis', {})
    default_envlist = get_default_envlist(version)
    return split_env(travis_section.get(version, default_envlist))


def match_envs(declared_envs, desired_envs):
    """Determine the envs that match the desired_envs.

    Envs in the desired_envs that do not match any env in the
    declared_envs are appended to the list of matches verbatim.
    """
    matched = [
        declared for declared in declared_envs
        if any(env_matches(declared, desired) for desired in desired_envs)
    ]
    unmatched = [
        desired for desired in desired_envs
        if not any(env_matches(declared, desired) for declared in declared_envs)
    ]
    return matched + unmatched


def env_matches(declared, desired):
    """Determine if a declared env matches a desired env.

    Rather than simply using the name of the env verbatim, take a
    closer look to see if all the desired factors are fulfilled. If
    the desired factors are fulfilled, but there are other factors,
    it should still match the env.
    """
    desired_factors = desired.split('-')
    declared_factors = declared.split('-')
    return all(factor in declared_factors for factor in desired_factors)
