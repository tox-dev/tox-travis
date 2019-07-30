"""Tests of the --travis-after flag."""
import pytest
import py
import subprocess
from contextlib import contextmanager
from tox_travis.after import (
    travis_after,
    after_config_matches,
)


ini = b"""
[tox]
envlist = py35, py36
"""

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


class TestAfter:
    """Test the logic of waiting for other jobs to finish."""

    def call(self, command):
        """Return the raw output of the given command."""
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

    @contextmanager
    def configure(self, tmpdir, monkeypatch, tox_ini, version):
        """Configure the environment for a test."""
        origdir = tmpdir.chdir()
        tmpdir.join('tox.ini').write(tox_ini)
        tmpdir.join('.coveragerc').write(coverage_config)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', version)

        yield

        # Change back to the original directory
        # Copy .coverage.* report files
        origdir.chdir()
        for f in tmpdir.listdir(lambda f: f.basename.startswith('.coverage.')):
            f.copy(origdir)

    def test_after_deprecated(self, tmpdir, monkeypatch):
        """Show deprecation message when using --travis-after."""
        with self.configure(tmpdir, monkeypatch, ini, '3.6'):
            _, _, stderr = self.call(['tox', '-l', '--travis-after'])
            assert 'The after all feature has been deprecated.' in stderr

    def test_pull_request(self, mocker, monkeypatch, capsys):
        """Pull requests should not run after-all."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('TRAVIS_PULL_REQUEST', '1')

        travis_after(mocker.Mock(), mocker.Mock())

        out, err = capsys.readouterr()
        assert out == ''
        assert err == ''

    def test_not_after_config_matches(self, mocker, monkeypatch, capsys):
        """Return silently when no config matches."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=False)
        monkeypatch.setenv('TRAVIS', 'true')
        travis_after(mocker.Mock(), mocker.Mock())

    def test_no_github_token(self, mocker, monkeypatch, capsys):
        """Raise with the right message when no github token."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 32
        out, err = capsys.readouterr()
        assert 'No GitHub token given.' in err

    def test_travis_environment_build_id(self, mocker, monkeypatch, capsys):
        """Raise with the right message when no build id."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 34
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_environment_job_number(self, mocker, monkeypatch, capsys):
        """Raise with the right message when no build id."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 34
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_environment_api_url(self, mocker, monkeypatch, capsys):
        """Raise with the right message when no api url."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '1234.1')
        # TRAVIS_API_URL is set to a reasonable default
        monkeypatch.setenv('TRAVIS_API_URL', '')
        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 34
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_env_polling_interval(self, mocker, monkeypatch, capsys):
        """Raise with the right message when no polling interval."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '1234.1')
        # TRAVIS_POLLING_INTERVAL is set to a reasonable default
        monkeypatch.setenv('TRAVIS_POLLING_INTERVAL', 'xbe')
        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 33
        out, err = capsys.readouterr()
        assert "Invalid polling interval given: 'xbe'" in err

    def test_travis_env_passed(self, mocker, monkeypatch, capsys):
        """Bahave when required environment is present and jobs pass."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '141739801')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '75.1')

        responses = [
            {'access_token': 'fakeaccesstoken'},
            {'annotations': [],
             'build': {'commit_id': 40173062,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'language': 'generic',
                                  'matrix': {'fast_finish': True},
                                  'os': ['linux', 'osx'],
                                  'script': 'env',
                                  'sudo': False},
                       'duration': 30,
                       'event_type': 'pull_request',
                       'finished_at': '2016-07-01T21:19:11Z',
                       'id': 141739801,
                       'job_ids': [141739802, 141739803],
                       'number': '75',
                       'pull_request': True,
                       'pull_request_number': 21,
                       'pull_request_title': 'View the travis env',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:18:03Z',
                       'state': 'passed'},
             'commit': {'author_email': 'ryan@ryanhiebert.com',
                        'author_name': 'Ryan Hiebert',
                        'branch': 'master',
                        'branch_is_default': True,
                        'committed_at': '2016-07-01T21:17:38Z',
                        'committer_email': 'ryan@ryanhiebert.com',
                        'committer_name': 'Ryan Hiebert',
                        'compare_url': 'https://github.com/tox-dev/tox-travis/pull/21',
                        'id': 40173062,
                        'message': 'Add languages to the mix',
                        'sha': 'f5ba1abff4fa27ea48bf3eac3a924477aea13dd8'},
             'jobs': [{'allow_failure': False,
                       'annotation_ids': [],
                       'build_id': 141739801,
                       'commit_id': 40173062,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'language': 'generic',
                                  'os': 'linux',
                                  'script': 'env',
                                  'sudo': False},
                       'finished_at': '2016-07-01T21:18:27Z',
                       'id': 141739802,
                       'log_id': 102977868,
                       'number': '75.1',
                       'queue': 'builds.docker',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:18:03Z',
                       'state': 'passed',
                       'tags': None},
                      {'allow_failure': False,
                       'annotation_ids': [],
                       'build_id': 141739801,
                       'commit_id': 40173062,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'language': 'generic',
                                  'os': 'osx',
                                  'script': 'env',
                                  'sudo': False},
                       'finished_at': '2016-07-01T21:19:11Z',
                       'id': 141739803,
                       'log_id': 102977869,
                       'number': '75.2',
                       'queue': 'builds.macstadium6',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:19:05Z',
                       'state': 'passed',
                       'tags': None}]},
        ]

        def get_json(url, auth=None, data=None):
            return next(get_json.responses)
        get_json.responses = iter(responses)

        mocker.patch('tox_travis.after.get_json', side_effect=get_json)
        travis_after(mocker.Mock(), mocker.Mock())
        out, err = capsys.readouterr()
        assert 'All required jobs were successful.' in out

    def test_travis_env_failed(self, mocker, monkeypatch, capsys):
        """Bahave when required environment is present and a job failed."""
        mocker.patch('tox_travis.after.after_config_matches',
                     return_value=True)
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '141739330')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '74.1')

        responses = [
            {'access_token': 'fakeaccesstoken'},
            {'annotations': [],
             'build': {'commit_id': 40172931,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'install': 'pip install .',
                                  'language': 'generic',
                                  'matrix': {'fast_finish': True},
                                  'os': ['linux', 'osx'],
                                  'script': 'env',
                                  'sudo': False},
                       'duration': 33,
                       'event_type': 'pull_request',
                       'finished_at': '2016-07-01T21:17:40Z',
                       'id': 141739330,
                       'job_ids': [141739331, 141739332],
                       'number': '74',
                       'pull_request': True,
                       'pull_request_number': 21,
                       'pull_request_title': 'View the travis env',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:16:32Z',
                       'state': 'errored'},
             'commit': {'author_email': 'ryan@ryanhiebert.com',
                        'author_name': 'Ryan Hiebert',
                        'branch': 'master',
                        'branch_is_default': True,
                        'committed_at': '2016-07-01T21:16:05Z',
                        'committer_email': 'ryan@ryanhiebert.com',
                        'committer_name': 'Ryan Hiebert',
                        'compare_url': 'https://github.com/tox-dev/tox-travis/pull/21',
                        'id': 40172931,
                        'message': 'Add languages to the mix',
                        'sha': '06e89f20adb11423a538f29d8144abcbe508d575'},
             'jobs': [{'allow_failure': False,
                       'annotation_ids': [],
                       'build_id': 141739330,
                       'commit_id': 40172931,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'install': 'pip install .',
                                  'language': 'generic',
                                  'os': 'linux',
                                  'script': 'env',
                                  'sudo': False},
                       'finished_at': '2016-07-01T21:16:56Z',
                       'id': 141739331,
                       'log_id': 102977517,
                       'number': '74.1',
                       'queue': 'builds.docker',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:16:32Z',
                       'state': 'errored',
                       'tags': None},
                      {'allow_failure': False,
                       'annotation_ids': [],
                       'build_id': 141739330,
                       'commit_id': 40172931,
                       'config': {'.result': 'configured',
                                  'branches': {'only': ['master']},
                                  'dist': 'precise',
                                  'group': 'stable',
                                  'install': 'pip install .',
                                  'language': 'generic',
                                  'os': 'osx',
                                  'script': 'env',
                                  'sudo': False},
                       'finished_at': '2016-07-01T21:17:40Z',
                       'id': 141739332,
                       'log_id': 102977518,
                       'number': '74.2',
                       'queue': 'builds.macstadium6',
                       'repository_id': 4857393,
                       'started_at': '2016-07-01T21:17:31Z',
                       'state': 'errored',
                       'tags': None}]},
        ]

        def get_json(url, auth=None, data=None):
            return next(get_json.responses)
        get_json.responses = iter(responses)

        mocker.patch('tox_travis.after.get_json', side_effect=get_json)

        with pytest.raises(SystemExit) as excinfo:
            travis_after(mocker.Mock(), mocker.Mock())

        assert excinfo.value.code == 35
        out, err = capsys.readouterr()
        assert 'Some jobs were not successful.' in out

    def test_after_config_matches_unconfigured(self):
        """Skip quickly when after section is unconfigured."""
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert not after_config_matches(ini, ['py36'])

    def test_after_config_matches_toxenv_match(self, capsys):
        """Test that it works using the legacy toxenv setting.

        It should also give a warning message.
        """
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'toxenv = py36\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert after_config_matches(ini, ['py36'])
        out, err = capsys.readouterr()
        msg = 'The "toxenv" key of the [travis:after] section is deprecated'
        assert msg in err

    def test_after_config_matches_toxenv_nomatch(self, capsys):
        """Test that it doesn't work using the legacy toxenv setting.

        It should also give a warning message.
        """
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'toxenv = py36\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert not after_config_matches(ini, ['py35'])
        out, err = capsys.readouterr()
        msg = 'The "toxenv" key of the [travis:after] section is deprecated'
        assert msg in err

    def test_after_config_matches_envlist_match(self):
        """Test that it works."""
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'envlist = py36\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert after_config_matches(ini, ['py36'])

    def test_after_config_matches_envlist_nomatch(self):
        """Test that it doesn't work."""
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'envlist = py36\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert not after_config_matches(ini, ['py35'])

    def test_after_config_matches_env_match(self, monkeypatch):
        """Test that it works."""
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.6')
        monkeypatch.setenv('DJANGO', '1.11')
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'travis =\n'
            '    python: 3.6\n'
            'env =\n'
            '    DJANGO: 1.11\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert after_config_matches(ini, ['py36'])

    def test_after_config_matches_env_nomatch(self, monkeypatch):
        """Test that it doesn't work."""
        monkeypatch.setenv('TRAVIS_PYTHON_VERSION', '3.5')
        monkeypatch.setenv('DJANGO', '1.11')
        inistr = (
            '[tox]\n'
            'envlist = py36\n'
            '\n'
            '[travis:after]\n'
            'travis =\n'
            '    python: 3.6\n'
            'env =\n'
            '    DJANGO: 1.11\n'
        )
        ini = py.iniconfig.IniConfig('', data=inistr)
        assert not after_config_matches(ini, ['py35'])
