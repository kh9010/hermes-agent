"""kh9010 fork, 2026-11-23: a restart must not silently drop interrupted work on chat platforms.

Evidence (state.db + raw.db, Aug-Sep 2026): eight WhatsApp turns were cut off by a gateway restart and
the resumed turn answered "Session restored successfully. I'm not resuming the interrupted work. What
would you like to do next?" (2026-08-12) or a variant. The upstream interactive note told the model to
"skip any unfinished work", so the work only came back when Kahran asked again, 15-35 minutes later.

These tests pin the wording contract of ``build_resume_recovery_note`` on interactive platforms:
say what was interrupted, finish read-only steps, ask before anything with side effects, never repeat
a side-effecting call blindly. The non-interactive branch (#57056) is unchanged and pinned upstream.
"""

from gateway.run import build_resume_recovery_note


def _auto_resume_note():
    return build_resume_recovery_note("restart_timeout", "", interactive=True)


def test_interactive_auto_resume_no_longer_drops_the_work():
    note = _auto_resume_note()
    assert "skip any unfinished work" not in note
    assert "ask what they would like to do next" not in note


def test_interactive_auto_resume_names_what_was_interrupted():
    note = _auto_resume_note()
    assert "what was in progress and how far it got" in note


def test_interactive_auto_resume_continues_read_only_steps():
    note = _auto_resume_note()
    assert "only read or check things" in note
    assert "continue them now" in note


def test_interactive_auto_resume_asks_before_side_effects():
    note = _auto_resume_note()
    for effect in ("sending or posting a message", "committing", "merging", "deploying",
                   "changing config", "restarting anything"):
        assert effect in note, effect
    assert "stop and ask the user whether to continue" in note


def test_interactive_auto_resume_never_blindly_repeats_side_effects():
    note = _auto_resume_note()
    assert "results already appear in the history" in note
    assert "may or may not have happened" in note


def test_new_message_after_restart_offers_the_unfinished_work():
    note = build_resume_recovery_note("restart_timeout", "hi", interactive=True)
    assert "Address the user's NEW message below FIRST" in note
    assert "offer to continue it" in note
    assert "skip any unfinished work" not in note
    # Still no unprompted re-execution when the user has said something new.
    assert "Do NOT re-execute old tool calls" in note
    assert note.endswith("\n\nhi")


def test_restart_command_is_still_never_rerun():
    for interactive in (True, False):
        for message in ("", "hi"):
            note = build_resume_recovery_note("shutdown_timeout", message, interactive=interactive)
            assert "do NOT re-execute or verify it" in note


def test_non_interactive_branch_unchanged():
    note = build_resume_recovery_note("restart_timeout", "", interactive=False)
    assert "CONTINUE the interrupted task to completion" in note
    assert "stop and ask the user" not in note
