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

    version = os.environ.get('TRAVIS_PYTHON_VERSION')

    config = py.iniconfig.IniConfig('tox.ini')
    travis_section = config.sections.get('tox:travis', {})
    tox_section = config.sections.get('tox', {})

    # Find the envs that tox knows about
    envlist = split_env(tox_section.get('envlist', []))

    # Find and expand the requested envs
    envstr = travis_section.get(version, TOX_DEFAULTS.get(version))
    desired_envlist = split_env(envstr)

    matched = [
        env for env in envlist if any(
            env_matches(env, desired_env)
            for desired_env in desired_envlist
        )
    ]

    # If no envs match, just use the desired envstr directly
    if not matched:
        matched = [envstr]

    os.environ.setdefault('TOXENV', ','.join(matched))


def env_matches(env, desired_env):
    """Determine if an env matches a desired env.

    Rather than simply using the name of the env verbatim, take a
    closer look to see if all the desired factors are fulfilled. If
    the desired factors are fulfilled, but there are other factors,
    it should still match the env.
    """
    desired_factors = desired_env.split('-')
    env_factors = env.split('-')
    return all(factor in env_factors for factor in desired_factors)
