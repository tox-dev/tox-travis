"""Seamless integration of Tox into Travis CI."""
import os
import py
import tox


@tox.hookimpl
def tox_addoption(parser):
    if 'TRAVIS' not in os.environ:
        return

    version = os.environ.get('TRAVIS_PYTHON_VERSION')

    config = py.iniconfig.IniConfig('tox.ini')
    section = config.sections.get('tox:travis', {})
    envlist = section.get(version)

    if envlist:
        os.environ.setdefault('TOXENV', envlist)
