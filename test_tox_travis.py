import os
import subprocess


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
envlist = py34, py34-docs, py34-django
"""

tox_ini_factors_override = tox_ini_factors + b"""
[tox:travis]
2.7 = py27-django
"""

tox_ini_django_factors = b"""
[tox]
envlist = py{27,34}-django, other

[tox:travis]
2.7 = django
3.4 = other
"""


class TestToxTravis:
    def test_not_travis(self, tmpdir):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        output = subprocess.check_output(['tox', '-l'])
        expected = '\n'.join([
            'py26', 'py27',
            'py32', 'py33', 'py34',
            'pypy', 'pypy3',
            'docs'
        ]) + '\n'  # Expect a trailing newline
        assert output.decode('utf-8') == expected

    def test_travis_default_26(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.6')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py26\n'

    def test_travis_default_27(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py27\n'

    def test_travis_default_32(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.2')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py32\n'

    def test_travis_default_33(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.3')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py33\n'

    def test_travis_default_34(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.4')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py34\n'

    def test_travis_default_pypy(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', 'pypy')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'pypy\n'

    def test_travis_default_pypy3(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', 'pypy3')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'pypy3\n'

    def test_travis_override(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_override)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py27\ndocs\n'

    def test_respect_overridden_toxenv(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        monkeypatch.setenv('TOXENV', 'py32')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py32\n'

    def test_keep_if_no_match(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_factors)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py27\n'

    def test_default_tox_ini_overrides(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_factors_override)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py27-django\n'

    def test_factors(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_factors)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.4')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py34\npy34-docs\npy34-django\n'

    def test_django_factors(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_django_factors)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '2.7')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'py27-django\npy34-django\n'

    def test_non_python_factor(self, tmpdir, monkeypatch):
        os.chdir(str(tmpdir))
        tmpdir.join('tox.ini').write(tox_ini_django_factors)

        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.4')
        output = subprocess.check_output(['tox', '-l'])
        assert output.decode('utf-8') == 'other\n'
