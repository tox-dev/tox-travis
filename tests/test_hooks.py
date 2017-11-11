from tox_travis.hooks import tox_subcommand_test_post


class TestToxSubcommandTestPost:
    def test_tox_subcommand_test_post_enabled(self, mocker):
        travis_after = mocker.patch('tox_travis.hooks.travis_after')
        config = mocker.Mock()
        config.option.travis_after = True
        tox_subcommand_test_post(config)
        travis_after.assert_called_once_with(config._cfg, config.envlist)

    def test_tox_subcommand_test_post_not_enabled(self, mocker):
        travis_after = mocker.patch('tox_travis.hooks.travis_after')
        config = mocker.Mock()
        config.option.travis_after = False
        tox_subcommand_test_post(config)
        assert not travis_after.called
