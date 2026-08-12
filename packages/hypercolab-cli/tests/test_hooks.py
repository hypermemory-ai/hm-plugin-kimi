from hypercolab_cli import hooks
from hypercolab_cli.hooks import evaluate_client_hook


def test_read_only_shell_is_allowed():
    assert (
        evaluate_client_hook(
            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}}
        )
        == {}
    )


def test_unknown_writing_shell_command_is_blocked():
    result = evaluate_client_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "sed -i '' s/old/new/ src/app.py"},
        }
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_git_push_attempt_and_result_are_structured(monkeypatch):
    events = []

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def log_activity(self, **event):
            events.append(event)

    monkeypatch.setattr(hooks, "HypercolabClient", _Client)
    before = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git push origin colab"},
    }
    after = {
        **before,
        "hook_event_name": "PostToolUse",
        "tool_response": {"exit_code": 0, "output": "raw output must not be logged"},
    }

    assert evaluate_client_hook(before) == {}
    assert evaluate_client_hook(after) == {}
    assert [event["kind"] for event in events] == ["git.push_attempted", "git.push_completed"]
    assert all("output" not in event["metadata"] for event in events)
