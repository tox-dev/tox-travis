import os
import sys
import re
import py
import tox

from itertools import product

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


def _legacy_get_desired_envs(config, version):
    travis_section = config.sections.get('tox:travis', {})
    default_envlist = get_default_envlist(version)
    return split_env(travis_section.get(version, default_envlist))


def get_desired_envs(config, version):
    """Get the expanded list of desired envs."""
    if 'tox:travis' in config.sections:
        return _legacy_get_desired_envs(config, version)

    # Parse the travis section
    travis_section = config.sections.get('travis', {})
    default_envlist = get_default_envlist(version)
    default_envlist = split_env(default_envlist)

    # Get python version factors
    python_factors = parse_dict(travis_section.get('python', ''))
    python_factors = python_factors.get(version, '')
    python_factors = split_env(python_factors)

    # Get os version factors
    os_factors = parse_dict(travis_section.get('os', ''))
    os_factors = os_factors.get(os.environ.get('TRAVIS_OS_NAME'), '')
    os_factors = split_env(os_factors)

    # Combine python & os version factors
    desired_factors = [
        (python_factors + os_factors) or default_envlist
    ]

    # Parse the environment factors
    env_section = config.sections.get('travis:env', {})

    # Use the travis section and environment variables
    # to determine the desired tox factors.
    desired_factors += [
        get_env_factors(env_section, envvar)
        for envvar in env_section
    ]

    # filter empty factors and join
    return reduce_factors(filter(None, desired_factors))


def get_env_factors(env_section, envvar):
    """Derive a list of tox factors from the travis:env section
    using the current environment variables. For example, given
    the following travis:env section:

        [travis:env]
        DJANGO =
            1.9: django19
            1.10: django110

    If the current environment defines DJANGO as '1.9', then getting the
    DJANGO envvar would return a ['django19'] factor list.

    """
    env_factors = parse_dict(env_section.get(envvar, ''))
    return env_factors.get(os.environ.get(envvar))


def parse_dict(value):
    """Parse a dict value from the tox config. Values support comma
    separation and brace expansion. ex:

        python =
            2.7: py27, docs
            3: py{35,36}

        >>> parse_dict("2.7: py27, docs\n3: py{35,36}")
        {'2.7': ['py27', 'docs'], '3': ['py35', 'py36']}

    """
    # key-value pairs are split by line, may contain extraneous whitespace
    kv_pairs = [line.strip() for line in value.splitlines()]
    kv_pairs = [kv.strip().split(':', 1) for kv in kv_pairs if kv]

    # values may be comma-separated
    return dict(
        (key.strip(), split_env(value))
        for key, value in kv_pairs
    )


def reduce_factors(factors):
    """Reduce sets of factors into a single list of envs.

        >>> reduce_factors([['py27', 'py35'], ['django110']])
        ['py27-django110', 'py35-django110']

    """
    envs = product(*factors)
    envs = ['-'.join(env) for env in envs]
    return envs


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
