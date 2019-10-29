"""Test the automatic toxenv feature of Tox-Travis."""
import py
import re
import subprocess
import pytest
from contextlib import contextmanager


coverage_config = b"""
[run]
branch = True
parallel = True
source = tox_travis

[paths]
source =
    src
    */site-packages
"""


tox_ini = b"""
[tox]
envlist = py36, py37, pypy, pypy3, docs
"""

tox_ini_override = tox_ini + b"""
[tox:travis]
3.6 = py36, docs
"""

tox_ini_factors = b"""
[tox]
envlist = py37, py37-docs, py37-django, dontmatch-1
"""

tox_ini_factors_override = tox_ini_factors + b"""
[tox:travis]
3.6 = py36-django
"""

tox_ini_factors_override_nonenvlist = tox_ini_factors + b"""
[tox:travis]
3.7 = py37, extra

[testenv:extra-coveralls]
basepython=python3.7

[testenv:extra-flake8]
basepython=python3.7

[testenv:dontmatch-2]
basepython=python3.7
"""

tox_ini_django_factors = b"""
[tox]
envlist = py{36,37}-django, other

[tox:travis]
3.6 = django
3.7 = other
"""

tox_ini_travis_factors = b"""
[tox]
envlist = py{35,36,37}, docs

[travis]
language =
    generic: py{36,37}, docs
python =
    3.6: py36, docs
os =
    osx: py{36,37}, docs
"""

tox_ini_travis_env = b"""
[tox]
envlist = py{36,37}-django{21,22}

[travis:env]
DJANGO =
    2.1: django21
    2.2: django22
"""

tox_ini_legacy_warning = b"""
[tox]
envlist = py{36,37}-django{21,22}

[tox:travis]
3.7 = py37, extra

[travis:env]
DJANGO =
    2.1: django21
    2.2: django22
"""

tox_ini_ignore_outcome = b"""
[tox]
envlist = py{35,36,37}

[testenv]
ignore_outcome = True
"""

tox_ini_ignore_outcome_unignore_outcomes = tox_ini_ignore_outcome + b"""
[travis]
unignore_outcomes = True
"""

tox_ini_ignore_outcome_not_unignore_outcomes = tox_ini_ignore_outcome + b"""
[travis]
unignore_outcomes = False
"""


class TestToxEnv:
    """Test the logic to automatically configure TOXENV with Travis."""

    def tox_envs(self, **kwargs):
        """Find the envs that tox sees."""
        returncode, stdout, stderr = self.tox_envs_raw(**kwargs)
        assert returncode == 0, stderr
        return [env for env in stdout.strip().splitlines()]

    def tox_envs_raw(self, ini_filename=None):
        """Return the raw output of finding what tox sees."""
        command = ['tox', '-l']
        if ini_filename is not None:
            command += ['-c', ini_filename]
        return self.call_raw(command)

    def tox_config(self, **kwargs):
        """Returns the configuration per configuration as computed by tox."""
        returncode, stdout, stderr = self.tox_config_raw(**kwargs)
        assert returncode == 0, stderr
        ini = "[global]\n" + re.sub(
            re.compile(r'^\s+', re.MULTILINE), '', stdout)
        return py.iniconfig.IniConfig('', data=ini)

    def tox_config_raw(self, ini_filename=None):
        """Return the raw output of finding the complex tox env config."""
        command = ['tox', '--showconfig']
        if ini_filename is not None:
            command += ['-c', ini_filename]
        return self.call_raw(command)

    def call_raw(self, command):
        """Return the raw output of the given command."""
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

    @contextmanager  # noqa - complexity
    def configure(self, tmpdir, monkeypatch, tox_ini,
                  version=None, major=None, minor=None,
                  travis_version=None, travis_os=None,
                  travis_language=None, env=None,
                  ini_filename='tox.ini'):
        """Configure the environment for running a test."""
        origdir = tmpdir.chdir()
        tmpdir.join(ini_filename).write(tox_ini)
        tmpdir.join('.coveragerc').write(coverage_config)

        if version or travis_version or travis_os or travis_language:
            monkeypatch.setenv('TRAVIS', 'true')

        if version:
            sys_version = '{version},{major},{minor}'.format(
                version=version, major=major, minor=minor)
            if not travis_version:
                travis_version = '{major}.{minor}'.format(
                    major=major, minor=minor)
                if version == 'PyPy':
                    travis_version = 'pypy3' if major == 3 else 'pypy'

            monkeypatch.setenv('__TOX_TRAVIS_SYS_VERSION', sys_version)

        if travis_version:
            monkeypatch.setenv('TRAVIS_PYTHON_VERSION', travis_version)

        if travis_os:
            monkeypatch.setenv('TRAVIS_OS_NAME', travis_os)

        if travis_language:
            monkeypatch.setenv('TRAVIS_LANGUAGE', travis_language)

        if isinstance(env, dict):
            for key, value in env.items():
                monkeypatch.setenv(key, value)

        yield

        # Change back to the original directory
        # Copy .coverage.* report files
        origdir.chdir()
        for f in tmpdir.listdir(lambda f: f.basename.startswith('.coverage.')):
            f.copy(origdir)

    def test_not_travis(self, tmpdir, monkeypatch):
        """Test the results if it's not on a Travis worker."""
        with self.configure(tmpdir, monkeypatch, tox_ini):
            expected = ['py36', 'py37', 'pypy', 'pypy3', 'docs']
            assert self.tox_envs() == expected

    def test_travis_config_filename(self, tmpdir, monkeypatch):
        """Give the correct env for manual filename."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6,
                            ini_filename='spam.ini'):
            assert self.tox_envs(ini_filename='spam.ini') == ['py36']

    def test_travis_default_36(self, tmpdir, monkeypatch):
        """Give the correct env for CPython 2.7."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            assert self.tox_envs() == ['py36']

    def test_travis_default_37(self, tmpdir, monkeypatch):
        """Give the correct env for CPython 3.7."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 7):
            assert self.tox_envs() == ['py37']

    def test_travis_default_pypy(self, tmpdir, monkeypatch):
        """Give the correct env for PyPy for Python 2.7."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'PyPy', 2, 7):
            assert self.tox_envs() == ['pypy']

    def test_travis_default_pypy3(self, tmpdir, monkeypatch):
        """Give the correct env for PyPy for Python 3.5."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'PyPy', 3, 5):
            assert self.tox_envs() == ['pypy3']

    def test_travis_python_version_py36(self, tmpdir, monkeypatch):
        """Give the correct env when python version is given by Travis."""
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.6'
        ):
            assert self.tox_envs() == ['py36']

    def test_travis_python_version_py35(self, tmpdir, monkeypatch):
        """Give the correct env when python version is given by Travis."""
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.5'
        ):
            assert self.tox_envs() == ['py35']

    def test_travis_python_version_pypy(self, tmpdir, monkeypatch):
        """Give the correct env when python version is given by Travis."""
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='pypy'
        ):
            assert self.tox_envs() == ['pypy']

    def test_travis_python_version_pypy3(self, tmpdir, monkeypatch):
        """Give the correct env when python version is given by Travis."""
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='pypy3'
        ):
            assert self.tox_envs() == ['pypy3']

    def test_travis_not_matching(self, tmpdir, monkeypatch):
        """TRAVIS_PYTHON_VERSION should be preferred.

        When that environment variable isn't set, we automatically
        generate a likely env to be the default. However, there
        are some cases where the TRAVIS_PYTHON_VERSION and the
        default python version may be different. Most notably,
        when using an ``os`` of ``osx``, which doesn't have
        support for the ``python`` factor.
        """
        with self.configure(
            tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6, '3.6'
        ):
            assert self.tox_envs() == ['py36']

    def test_travis_nightly(self, tmpdir, monkeypatch):
        """When nightly is specified, it should use sys.version_info."""
        with self.configure(
            tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6, 'nightly'
        ):
            assert self.tox_envs() == ['py36']

    def test_travis_override(self, tmpdir, monkeypatch):
        """Test when the setting is overridden for a particular Python."""
        tox_ini = tox_ini_override
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            assert self.tox_envs() == ['py36', 'docs']

    # XFAIL because of changes to tox -l to make it show declared envs
    # rather than the envs that will actually run, which is what we
    # need to test. When a better option is available, we can get this
    # test working again.
    #
    # # https://github.com/tox-dev/tox/pull/1284#issuecomment-488411553
    @pytest.mark.xfail
    def test_respect_overridden_toxenv(self, tmpdir, monkeypatch):
        """Ensure that TOXENV if given is not changed."""
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            monkeypatch.setenv('TOXENV', 'py32')
            assert self.tox_envs() == ['py32']

    def test_keep_if_no_match(self, tmpdir, monkeypatch):
        """It should keep the desired env if no declared env matches."""
        tox_ini = tox_ini_factors
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            assert self.tox_envs() == ['py36']

    def test_default_tox_ini_overrides(self, tmpdir, monkeypatch):
        """Keep the overridden envlist verbatim when no envlist is declared."""
        tox_ini = tox_ini_factors_override
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            assert self.tox_envs() == ['py36-django']

    def test_factors(self, tmpdir, monkeypatch):
        """Test that it will match envs by factors."""
        tox_ini = tox_ini_factors
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 7):
            assert self.tox_envs() == ['py37', 'py37-docs', 'py37-django']

    def test_match_and_keep(self, tmpdir, monkeypatch):
        """Match factors for envs declared outside of envlist."""
        tox_ini = tox_ini_factors_override_nonenvlist
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 7):
            assert self.tox_envs() == ['py37', 'py37-docs', 'py37-django',
                                       'extra-coveralls', 'extra-flake8']

    def test_django_factors(self, tmpdir, monkeypatch):
        """A non-default factor completely overrides the default factor."""
        tox_ini = tox_ini_django_factors
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 6):
            assert self.tox_envs() == ['py36-django', 'py37-django']

    def test_non_python_factor(self, tmpdir, monkeypatch):
        """A non-default factor completely overrides the default factor."""
        tox_ini = tox_ini_django_factors
        with self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 7):
            assert self.tox_envs() == ['other']

    def test_travis_factors_py36(self, tmpdir, monkeypatch):
        """Test python factor given in the new travis section."""
        tox_ini = tox_ini_travis_factors
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.6'
        ):
            assert self.tox_envs() == ['py36', 'docs']

    def test_travis_factors_py37(self, tmpdir, monkeypatch):
        """Test python factor given in the new travis section."""
        tox_ini = tox_ini_travis_factors
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.7'
        ):
            assert self.tox_envs() == ['py37']

    def test_travis_factors_osx(self, tmpdir, monkeypatch):
        """Test os factor given in the new travis section."""
        tox_ini = tox_ini_travis_factors
        with self.configure(tmpdir, monkeypatch, tox_ini, travis_os='osx'):
            assert self.tox_envs() == ['py36', 'py37', 'docs']

    def test_travis_factors_py36_osx(self, tmpdir, monkeypatch):
        """Test os and python factors given in the new travis section."""
        tox_ini = tox_ini_travis_factors
        with self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='3.6', travis_os='osx'
        ):
            assert self.tox_envs() == ['py36', 'docs']

    def test_travis_factors_language(self, tmpdir, monkeypatch):
        """Test language factor given in the new travis section."""
        tox_ini = tox_ini_travis_factors
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_language='generic'
        ):
            assert self.tox_envs() == ['py36', 'py37', 'docs']

    def test_travis_env_py36(self, tmpdir, monkeypatch):
        """Test that env factors are ignored if not fulfilled."""
        tox_ini = tox_ini_travis_env
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.6'
        ):
            assert self.tox_envs() == ['py36-django21', 'py36-django22']

    def test_travis_env_py36_dj21(self, tmpdir, monkeypatch):
        """Test that env factors are used if they match."""
        tox_ini = tox_ini_travis_env
        with self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='3.6', env={'DJANGO': '2.1'}
        ):
            assert self.tox_envs() == ['py36-django21']

    def test_travis_env_py37_dj22(self, tmpdir, monkeypatch):
        """Test that env factors are used if they match."""
        tox_ini = tox_ini_travis_env
        with self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='3.7', env={'DJANGO': '2.2'}
        ):
            assert self.tox_envs() == ['py37-django22']

    def test_legacy_warning(self, tmpdir, monkeypatch):
        """Using the legacy tox:travis section prints a warning on stderr."""
        tox_ini = tox_ini_legacy_warning
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.6'
        ):
            _, _, stderr = self.tox_envs_raw()
            assert (
                'The [tox:travis] section is deprecated in favor of the '
                '"python" key of the [travis] section.' in stderr)

    def test_travis_ignore_outcome(self, tmpdir, monkeypatch):
        """Test ignore_outcome without setting obey_outcomes."""
        tox_ini = tox_ini_ignore_outcome
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.7'
        ):
            config = self.tox_config()
            assert config["testenv:py37"]["ignore_outcome"] == "True"

    def test_travis_ignore_outcome_unignore_outcomes(self, tmpdir,
                                                     monkeypatch):
        """Test ignore_outcome setting unignore_outcomes = False."""
        tox_ini = tox_ini_ignore_outcome_unignore_outcomes
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.7'
        ):
            config = self.tox_config()
            assert config["testenv:py37"]["ignore_outcome"] == "False"

    def test_travis_ignore_outcome_not_unignore_outcomes(self, tmpdir,
                                                         monkeypatch):
        """Test ignore_outcome setting unignore_outcomes = False (default)."""
        tox_ini = tox_ini_ignore_outcome_not_unignore_outcomes
        with self.configure(
            tmpdir, monkeypatch, tox_ini, travis_version='3.7'
        ):
            config = self.tox_config()
            assert config["testenv:py37"]["ignore_outcome"] == "True"

    def test_local_ignore_outcome_unignore_outcomes(self, tmpdir, monkeypatch):
        """Test ignore_outcome unchanged when testing locally."""
        tox_ini = tox_ini_ignore_outcome_unignore_outcomes
        with self.configure(tmpdir, monkeypatch, tox_ini):
            config = self.tox_config()
            assert config["testenv:py37"]["ignore_outcome"] == "True"
