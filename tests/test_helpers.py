from tox_travis import parse_dict, reduce_factors


class TestParseDict:

    def test_simple(self):
        value = """
        1.9: django19
        1.10: django110
        """
        expected = {
            '1.9': ['django19'],
            '1.10': ['django110'],
        }

        assert parse_dict(value) == expected

    def test_comma_separated_list(self):
        value = """
        2.7: py27, docs
        3.5: py35
        """
        expected = {
            '2.7': ['py27', 'docs'],
            '3.5': ['py35'],
        }

        assert parse_dict(value) == expected

    def test_brace_expansion(self):
        value = """
        2.7: py27, docs
        3: py{35,36}
        """
        expected = {
            '2.7': ['py27', 'docs'],
            '3': ['py35', 'py36'],
        }

        assert parse_dict(value) == expected


class TestReduceFactors:

    def test_simple(self):
        factors = [
            ['py35'],
            ['django110'],
        ]
        expected = [
            'py35-django110',
        ]

        assert reduce_factors(factors) == expected

    def test_multiple(self):
        factors = [
            ['py27', 'py35'],
            ['django19'],
            ['drf33', 'drf34'],
        ]
        expected = [
            'py27-django19-drf33',
            'py27-django19-drf34',
            'py35-django19-drf33',
            'py35-django19-drf34',
        ]

        assert reduce_factors(factors) == expected
