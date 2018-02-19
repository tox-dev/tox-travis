from tox_travis.hacks import subcommand_test_monkeypatch


class TestSessionSubcommandTest:
    """Test the overridden post hook for subcommand_test."""

    def test_subcommand_test_post_hook(self, mocker):
        """It should return the same retcode, but run the hook."""
        subcommand_test = mocker.patch('tox.session.Session.subcommand_test',
                                       return_value=42)
        tox_subcommand_test_post = mocker.Mock()
        subcommand_test_monkeypatch(tox_subcommand_test_post)

        import tox.session
        session = mocker.Mock()

        real_subcommand_test = tox.session.Session.subcommand_test
        # Python 2 compat
        real_subcommand_test = getattr(
            real_subcommand_test, '__func__', real_subcommand_test)

        assert real_subcommand_test(session) == 42
        subcommand_test.assert_called_once_with(session)
        tox_subcommand_test_post.assert_called_once_with(session.config)
