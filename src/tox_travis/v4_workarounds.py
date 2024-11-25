import itertools
import re

_ENVSTR_SPLIT_PATTERN = re.compile(r"((?:{[^}]+})+)|,")
_ENVSTR_EXPAND_PATTERN = re.compile(r"{([^}]+)}")
_WHITESPACE_PATTERN = re.compile(r"\s+")

def mapcat(f, seq):
    return list(itertools.chain.from_iterable(map(f, seq)))


def _expand_envstr(envstr):
    # split by commas not in groups
    tokens = _ENVSTR_SPLIT_PATTERN.split(envstr)
    envlist = ["".join(g).strip() for k, g in itertools.groupby(tokens, key=bool) if k]

    def expand(env):
        tokens = _ENVSTR_EXPAND_PATTERN.split(env)
        parts = [_WHITESPACE_PATTERN.sub("", token).split(",") for token in tokens]
        return ["".join(variant) for variant in itertools.product(*parts)]

    return mapcat(expand, envlist)

def _split_env(env):
    """if handed a list, action="append" was used for -e"""
    if env is None:
        return []
    if not isinstance(env, list):
        env = [e.split("#", 1)[0].strip() for e in env.split("\n")]
        env = ",".join(e for e in env if e)
        env = [env]
    return mapcat(_expand_envstr, env)
