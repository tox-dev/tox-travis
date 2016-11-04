import os
import subprocess

from pytest import raises


tox_ini = b"""
[tox]
envlist = py26, py27, py32, py33, py34, pypy, pypy3, docs
"""

tox_ini_override = tox_ini + b"""
[tox:travis]
2.7 = py27, docs
"""

tox_ini_factors = b"""
[tox]
envlist = py34, py34-docs, py34-django, dontmatch-1
"""

tox_ini_factors_override = tox_ini_factors + b"""
[tox:travis]
2.7 = py27-django
"""

tox_ini_factors_override_nonenvlist = tox_ini_factors + b"""
[tox:travis]
3.4 = py34, extra

[testenv:extra-coveralls]
basepython=python3.4

[testenv:extra-flake8]
basepython=python3.4

[testenv:dontmatch-2]
basepython=python3.4
"""

tox_ini_django_factors = b"""
[tox]
envlist = py{27,34}-django, other

[tox:travis]
2.7 = django
3.4 = other
"""

tox_ini_travis_factors = b"""
[tox]
envlist = py{27,34,35}, docs

[travis]
language =
    generic: py{27,35}, docs
python =
    2.7: py27, docs
os =
    osx: py{27,35}, docs
"""

tox_ini_travis_env = b"""
[tox]
envlist = py{27,35}-django{19,110}

[travis:env]
DJANGO =
    1.9: django19
    1.10: django110
"""

tox_ini_legacy_warning = b"""
[tox]
envlist = py{27,35}-django{19,110}

[tox:travis]
3.4 = py34, extra

[travis:env]
DJANGO =
    1.9: django19
    1.10: django110
"""


class TestToxTravis:
    def tox_envs(self):
        """Find the envs that tox sees."""
        returncode, stdout, stderr = self.tox_envs_raw()
        assert returncode == 0, stderr
        return [env for env in stdout.strip().split('\n')]

    def tox_envs_raw(self):
        """Return the raw output of finding what tox sees."""
        proc = subprocess.Popen(
            ['tox', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

    def configure(self, tmpdir, monkeypatch, tox_ini,
                  version=None, major=None, minor=None,
                  travis_version=None, travis_os=None,
                  travis_language=None, env=None):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

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

        print('!!travis_version:', travis_version)

        if travis_version:
            monkeypatch.setenv('TRAVIS_PYTHON_VERSION', travis_version)

        if travis_os:
            monkeypatch.setenv('TRAVIS_OS_NAME', travis_os)

        if travis_language:
            monkeypatch.setenv('TRAVIS_LANGUAGE', travis_language)

        if isinstance(env, dict):
            for key, value in env.items():
                monkeypatch.setenv(key, value)

    def test_not_travis(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini)
        expected = [
            'py26', 'py27', 'py32', 'py33', 'py34',
            'pypy', 'pypy3', 'docs',
        ]
        assert self.tox_envs() == expected

    def test_travis_default_26(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 6)
        assert self.tox_envs() == ['py26']

    def test_travis_default_27(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        assert self.tox_envs() == ['py27']

    def test_travis_default_32(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 2)
        assert self.tox_envs() == ['py32']

    def test_travis_default_33(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 3)
        assert self.tox_envs() == ['py33']

    def test_travis_default_34(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 4)
        assert self.tox_envs() == ['py34']

    def test_travis_default_pypy(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'PyPy', 2, 7)
        assert self.tox_envs() == ['pypy']

    def test_travis_default_pypy3(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'PyPy', 3, 2)
        assert self.tox_envs() == ['pypy3']

    def test_travis_python_version_py27(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='2.7')
        assert self.tox_envs() == ['py27']

    def test_travis_python_version_py35(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='3.5')
        assert self.tox_envs() == ['py35']

    def test_travis_python_version_pypy(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='pypy')
        assert self.tox_envs() == ['pypy']

    def test_travis_python_version_pypy3(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='pypy3')
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
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7, '3.5')
        assert self.tox_envs() == ['py35']

    def test_travis_nightly(self, tmpdir, monkeypatch):
        """When nightly is specified, it should use sys.version_info."""
        self.configure(tmpdir, monkeypatch, tox_ini,
                       'CPython', 3, 5, 'nightly')
        assert self.tox_envs() == ['py35']

    def test_travis_override(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_override
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        assert self.tox_envs() == ['py27', 'docs']

    def test_respect_overridden_toxenv(self, tmpdir, monkeypatch):
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        monkeypatch.setenv('TOXENV', 'py32')
        assert self.tox_envs() == ['py32']

    def test_keep_if_no_match(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_factors
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        assert self.tox_envs() == ['py27']

    def test_default_tox_ini_overrides(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_factors_override
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        assert self.tox_envs() == ['py27-django']

    def test_factors(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_factors
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 4)
        assert self.tox_envs() == ['py34', 'py34-docs', 'py34-django']

    def test_match_and_keep(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_factors_override_nonenvlist
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 4)
        assert self.tox_envs() == ['py34', 'py34-docs', 'py34-django',
                                   'extra-coveralls', 'extra-flake8']

    def test_django_factors(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_django_factors
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 2, 7)
        assert self.tox_envs() == ['py27-django', 'py34-django']

    def test_non_python_factor(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_django_factors
        self.configure(tmpdir, monkeypatch, tox_ini, 'CPython', 3, 4)
        assert self.tox_envs() == ['other']

    def test_travis_factors_py27(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_factors
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='2.7')
        assert self.tox_envs() == ['py27', 'docs']

    def test_travis_factors_py35(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_factors
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='3.5')
        assert self.tox_envs() == ['py35']

    def test_travis_factors_osx(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_factors
        self.configure(tmpdir, monkeypatch, tox_ini, travis_os='osx')
        assert self.tox_envs() == ['py27', 'py35', 'docs']

    def test_travis_factors_py27_osx(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_factors
        self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='2.7', travis_os='osx')
        assert self.tox_envs() == ['py27', 'docs']

    def test_travis_factors_language(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_factors
        self.configure(
            tmpdir, monkeypatch, tox_ini, travis_language='generic')
        assert self.tox_envs() == ['py27', 'py35', 'docs']

    def test_travis_env_py27(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_env
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='2.7')
        assert self.tox_envs() == ['py27-django19', 'py27-django110']

    def test_travis_env_py27_dj19(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_env
        self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='2.7', env={'DJANGO': '1.9'})
        assert self.tox_envs() == ['py27-django19']

    def test_travis_env_py35_dj110(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_travis_env
        self.configure(
            tmpdir, monkeypatch, tox_ini,
            travis_version='3.5', env={'DJANGO': '1.10'})
        assert self.tox_envs() == ['py35-django110']

    def test_legacy_warning(self, tmpdir, monkeypatch):
        tox_ini = tox_ini_legacy_warning
        self.configure(tmpdir, monkeypatch, tox_ini, travis_version='2.7')

        _, _, stderr = self.tox_envs_raw()
        assert (
            'The [tox:travis] section is deprecated in favor of the '
            '"python" key of the [travis] section.' in stderr)
