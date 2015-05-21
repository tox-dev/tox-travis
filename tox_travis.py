import os
import py
import tox


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
    section = config.sections.get('tox:travis', {})
    envlist = section.get(version, TOX_DEFAULTS.get(version))

    if envlist:
        os.environ.setdefault('TOXENV', envlist)
