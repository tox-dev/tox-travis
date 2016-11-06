"""Make it easy to work with Tox and Travis."""
from __future__ import print_function
from itertools import product
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


# Mapping Travis factors to the associated env variables
TRAVIS_FACTORS = {
    'os': 'TRAVIS_OS_NAME',
    'language': 'TRAVIS_LANGUAGE',
    'python': 'TRAVIS_PYTHON_VERSION',
}


@tox.hookimpl
def tox_addoption(parser):
    """Default TOXENV automatically based on thes Travis environment."""
    if 'TRAVIS' not in os.environ:
        return

    if 'TOXENV' in os.environ:
        return  # Skip any processing if already set

    config = py.iniconfig.IniConfig('tox.ini')

    # Find the envs that tox knows about
    declared_envs = get_declared_envs(config)

    # Find all the envs for all the desired factors given
    desired_factors = get_desired_factors(config)

    # Reduce desired factors
    desired_envs = ['-'.join(env) for env in product(*desired_factors)]

    # Find matching envs
    matched = match_envs(declared_envs, desired_envs,
                         passthru=len(desired_factors) == 1)
    os.environ.setdefault('TOXENV', ','.join(matched))

    # Travis virtualenv do not provide `pypy3`, which tox tries to execute.
    # This doesnt affect Travis python version `pypy3`, as the pyenv pypy3
    # is in the PATH.
    # https://github.com/travis-ci/travis-ci/issues/6304
    # Force use of the virtualenv `python`.
    version = os.environ.get('TRAVIS_PYTHON_VERSION')
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


def get_desired_factors(config):
    """Get the list of desired envs per declared factor.

    Look at all the accepted configuration locations, and give a list
    of envlists, one for each Travis factor found.

    Look in the ``[travis]`` section for the known Travis factors,
    which are backed by environment variable checking behind the
    scenes, but provide a cleaner interface.

    Also look for the ``[tox:travis]`` section, which is deprecated,
    and treat it as an additional ``python`` key from the ``[travis]``
    section.

    Finally, look for factors based directly on environment variables,
    listed in the ``[travis:env]`` section. Configuration found in the
    ``[travis]`` and ``[tox:travis]`` sections are converted to this
    form under the hood, and are considered in the same way.

    Special consideration is given to the ``python`` factor. If this
    factor is set in the environment, then an appropriate configuration
    will be provided automatically if no manual configuration is
    provided.

    To allow for the most flexible processing, the envlists provided
    by each factor are not combined after they are selected, but
    instead returned as a list of envlists, and expected to be
    combined as and when appropriate by the caller. This allows for
    special handling based on the number of factors that were found
    to apply to this environment.
    """
    # Find configuration based on known travis factors
    travis_section = config.sections.get('travis', {})
    found_factors = [
        (factor, parse_dict(travis_section[factor]))
        for factor in TRAVIS_FACTORS
        if factor in travis_section
    ]

    # Backward compatibility with the old tox:travis section
    if 'tox:travis' in config.sections:
        print('The [tox:travis] section is deprecated in favor of'
              ' the "python" key of the [travis] section.', file=sys.stderr)
        found_factors.append(('python', config.sections['tox:travis']))

    # Inject any needed autoenv
    version = os.environ.get('TRAVIS_PYTHON_VERSION')
    if version:
        default_envlist = get_default_envlist(version)
        if not any(factor == 'python' for factor, _ in found_factors):
            found_factors.insert(0, ('python', {version: default_envlist}))
        python_factors = [(factor, mapping)
                          for factor, mapping in found_factors
                          if version and factor == 'python']
        for _, mapping in python_factors:
            mapping.setdefault(version, default_envlist)

    # Convert known travis factors to env factors,
    # and combine with declared env factors.
    env_factors = [
        (TRAVIS_FACTORS[factor], mapping)
        for factor, mapping in found_factors
    ] + [
        (name, parse_dict(value))
        for name, value in config.sections.get('travis:env', {}).items()
    ]

    # Choose the correct envlists based on the factor values
    return [
        split_env(mapping[os.environ[name]])
        for name, mapping in env_factors
        if name in os.environ and os.environ[name] in mapping
    ]


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


def match_envs(declared_envs, desired_envs, passthru):
    """Determine the envs that match the desired_envs.

    If ``passthru` is True, and none of the declared envs match the
    desired envs, then the desired envs will be used verbatim.

    :param declared_envs: The envs that are declared in the tox config.
    :param desired_envs: The envs desired from the tox-travis config.
    :param bool passthru: Whether to used the ``desired_envs`` as a
                          fallback if no declared envs match.
    """
    matched = [
        declared for declared in declared_envs
        if any(env_matches(declared, desired) for desired in desired_envs)
    ]
    return desired_envs if not matched and passthru else matched


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
