import sys

from setuptools import setup, __version__ as setuptools_version
from pkg_resources import parse_version

import pkg_resources

try:
    import _markerlib.markers
except ImportError:
    _markerlib = None


# _markerlib.default_environment() obtains its data from _VARS
# and wraps it in another dict, but _markerlib_evaluate writes
# to the dict while it is iterating the keys, causing an error
# on Python 3 only.
# Replace _markerlib.default_environment to return a custom dict
# that has all the necessary markers, and ignores any writes.

class Python3MarkerDict(dict):

    def __setitem__(self, key, value):
        pass

    def pop(self, i=-1):
        return self[i]


if _markerlib and sys.version_info[0] == 3:
    env = _markerlib.markers._VARS
    for key in list(env.keys()):
        new_key = key.replace('.', '_')
        if new_key != key:
            env[new_key] = env[key]

    _markerlib.markers._VARS = Python3MarkerDict(env)

    def default_environment():
        return _markerlib.markers._VARS

    _markerlib.default_environment = default_environment

# Avoid the very buggy pkg_resources.parser, which doesnt consistently
# recognise the markers needed by this setup.py
# Change this to setuptools 20.10.0 to support all markers.
if pkg_resources:
    if parse_version(setuptools_version) < parse_version('20.10.0'):
        MarkerEvaluation = pkg_resources.MarkerEvaluation

        del pkg_resources.parser
        pkg_resources.evaluate_marker = MarkerEvaluation._markerlib_evaluate
        MarkerEvaluation.evaluate_marker = MarkerEvaluation._markerlib_evaluate


def fread(fn):
    return open(fn, 'rb').read().decode('utf-8')

setup(
    name='tox-travis',
    description='Seamless integration of Tox into Travis CI',
    long_description=fread('README.rst') + '\n\n' + fread('HISTORY.rst'),
    author='Ryan Hiebert',
    author_email='ryan@ryanhiebert.com',
    url='https://github.com/ryanhiebert/tox-travis',
    license='MIT',
    version='0.6',
    package_dir={'': 'src'},
    py_modules=['tox_travis'],
    entry_points={
        'tox': ['travis = tox_travis'],
    },
    install_requires=['tox>=2.0'],
    extras_require={
        ':python_version=="3.2"': ['virtualenv<14', 'pytest<3'],
        ':platform_python_implementation=="PyPy" and python_version=="3.3"': ['virtualenv>=15.0.2'],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
