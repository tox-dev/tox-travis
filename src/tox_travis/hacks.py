import os

try:
    from tox.config import default_factors
except ImportError:
    default_factors = None


def pypy_version_monkeypatch():
    """Patch Tox to work with non-default PyPy 3 versions."""
    # Travis virtualenv do not provide `pypy3`, which tox tries to execute.
    # This doesnt affect Travis python version `pypy3`, as the pyenv pypy3
    # is in the PATH.
    # https://github.com/travis-ci/travis-ci/issues/6304
    # Force use of the virtualenv `python`.
    version = os.environ.get('TRAVIS_PYTHON_VERSION')
    if version and default_factors and version.startswith('pypy3.3-'):
        default_factors['pypy3'] = 'python'
