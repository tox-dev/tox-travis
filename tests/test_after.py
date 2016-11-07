"""Tests of the --travis-after flag."""
import pytest
from tox_travis.after import travis_after


class TestAfter:
    """Test the logic of waiting for other jobs to finish."""

    def test_not_travis(self, capsys):
        """Raise with the right message when not in Travis."""
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 2
        out, err = capsys.readouterr()
        assert 'Not a Travis environment.' in err

    def test_no_github_token(self, monkeypatch, capsys):
        """Raise with the right message when no github token."""
        monkeypatch.setenv('TRAVIS', 'true')
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 3
        out, err = capsys.readouterr()
        assert 'No GitHub token given.' in err

    def test_travis_environment_build_id(self, monkeypatch, capsys):
        """Raise with the right message when no build id."""
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 5
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_environment_job_number(self, monkeypatch, capsys):
        """Raise with the right message when no build id."""
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 5
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_environment_api_url(self, monkeypatch, capsys):
        """Raise with the right message when no api url."""
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '1234.1')
        # TRAVIS_API_URL is set to a reasonable default
        monkeypatch.setenv('TRAVIS_API_URL', '')
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 5
        out, err = capsys.readouterr()
        assert 'Required Travis environment not given.' in err

    def test_travis_environment_polling_interval(self, monkeypatch, capsys):
        """Raise with the right message when no polling interval."""
        monkeypatch.setenv('TRAVIS', 'true')
        monkeypatch.setenv('GITHUB_TOKEN', 'spamandeggs')
        monkeypatch.setenv('TRAVIS_BUILD_ID', '1234')
        monkeypatch.setenv('TRAVIS_JOB_NUMBER', '1234.1')
        # TRAVIS_POLLING_INTERVAL is set to a reasonable default
        monkeypatch.setenv('TRAVIS_POLLING_INTERVAL', 'xbe')
        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 4
        out, err = capsys.readouterr()
        assert "Invalid polling interval given: 'xbe'" in err

    def test_travis_environment_passed(self, monkeypatch, capsys, mocker):
        """Bahave when required environment is present and jobs pass."""
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
                        'compare_url': 'https://github.com/ryanhiebert/tox-travis/pull/21',  # noqa
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

        with pytest.raises(SystemExit) as excinfo:
            travis_after()

        assert excinfo.value.code == 0
        out, err = capsys.readouterr()
        assert 'All required jobs were successful.' in out

    def test_travis_environment_failed(self, monkeypatch, capsys, mocker):
        """Bahave when required environment is present and a job failed."""
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
                        'compare_url': 'https://github.com/ryanhiebert/tox-travis/pull/21',  # noqa
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
            travis_after()

        assert excinfo.value.code == 1
        out, err = capsys.readouterr()
        assert 'Some jobs were not successful.' in out
