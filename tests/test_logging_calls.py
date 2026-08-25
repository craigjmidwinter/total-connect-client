"""Static checks on this package's logging call sites.

`LOGGER.debug(msg, *args)` treats trailing positional arguments as %-format
arguments for `msg`. If `msg` carries no `%` placeholder, `msg % args` raises
`TypeError` when the record is formatted. Logging swallows that, so nothing
crashes -- but the intended line is never emitted and a `--- Logging error ---`
traceback goes to stderr instead, bypassing the logging system entirely.

That is silent in the worst way: it only bites on paths that are already
failing, which is exactly when the log line matters. This check is static
because the alternative -- capturing a malformed record with `caplog` -- makes
pytest fail during teardown reporting rather than through an assertion.
"""

import ast
import pathlib

LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "total_connect_client"


def _literal_message(node: ast.AST) -> str | None:
    """Return the literal text of a log message, or None if it is not a literal."""
    if isinstance(node, ast.JoinedStr):  # f-string: concatenate the constant parts
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _multi_arg_logging_calls():
    """Yield (path, lineno, level, message) for log calls with extra positional args."""
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr in LOG_METHODS):
                continue
            if len(node.args) < 2:
                continue
            yield path, node.lineno, func.attr, _literal_message(node.args[0])


def test_no_logging_call_passes_args_without_a_placeholder():
    """Every log call with extra positional args must have a %-placeholder message.

    Regression test for `client.py`'s HTTP-error line, which passed
    `response.content` as a second positional argument to an f-string message
    containing no `%`. It fired on every non-ok response -- the check runs
    before the 401 and retryable-status branches -- so during an outage the
    retry loop produced a stderr traceback per attempt and no usable log.
    """
    broken = [
        f"{path.name}:{lineno} LOGGER.{level}({message!r}, ...)"
        for path, lineno, level, message in _multi_arg_logging_calls()
        if message is not None and "%" not in message
    ]

    assert not broken, (
        "These logging calls pass positional args to a message with no % "
        "placeholder, so the record fails to format and is never emitted:\n  " + "\n  ".join(broken)
    )
