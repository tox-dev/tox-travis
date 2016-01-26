import os
import py
import tox

from tox.config import _split_env as split_env


TOX_DEFAULTS = {
    '2.6': 'py26',
    '2.7': 'py27',
    '3.2': 'py32',
    '3.3': 'py33',
    '3.4': 'py34',
    '3.5': 'py35',
    'pypy': 'pypy',
    'pypy3': 'pypy3',
}


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


def get_desired_envs(config, version):
    """Get the expanded list of desired envs."""
    travis_section = config.sections.get('tox:travis', {})
    return split_env(travis_section.get(version, TOX_DEFAULTS.get(version)))


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
