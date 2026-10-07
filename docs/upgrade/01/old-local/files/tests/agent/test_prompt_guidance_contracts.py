"""Contracts for rendered instructions, not source snapshots or LLM evaluations."""

import pytest

from agent import prompt_builder as pb


@pytest.fixture
def skills_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    skill = tmp_path / "skills" / "specialist" / "safe-work"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: safe-work\ndescription: Use before specialist actions.\n---\n"
        "Confirm scope before writes.\n"
    )
    pb.clear_skills_system_prompt_cache(clear_snapshot=True)
    yield pb.build_skills_system_prompt(available_tools={"terminal", "skill_view"})
    pb.clear_skills_system_prompt_cache(clear_snapshot=True)


def test_skill_loading_distinguishes_procedural_work_from_conversation(skills_prompt):
    assert "MUST load" in skills_prompt
    assert "clearly applicable procedural skills" in skills_prompt
    assert "before specialist work or actions" in skills_prompt
    assert "Casual conversation" in skills_prompt
    assert "tangential matches do not require a skill lookup" in skills_prompt
    assert "even partially relevant" not in skills_prompt
    assert "Err on the side of loading" not in skills_prompt
    assert "genuinely none are relevant" not in skills_prompt
    assert "domain safety" in skills_prompt
    assert "skill_manage(action='patch')" in skills_prompt
    assert "update it before finishing" in skills_prompt
    assert "safe-work" in skills_prompt
    assert "web_search" not in skills_prompt


@pytest.mark.parametrize(
    "guidance, obligations",
    [
        (pb.TASK_COMPLETION_GUIDANCE, (
            "working artifact", "real tool output", "stub", "report",
            "alternative", "NEVER", "fabricated", "blocker",
        )),
        (pb.TOOL_USE_ENFORCEMENT_GUIDANCE, (
            "MUST", "tool call", "same response", "final result",
        )),
        (pb.PARALLEL_TOOL_CALL_GUIDANCE, (
            "Independent", "single response", "depends", "read a file",
        )),
        (pb.OPENAI_MODEL_EXECUTION_GUIDANCE, (
            "correctness, completeness, or grounding", "empty, partial",
            "broader or different", "prerequisite", "dependency first",
            "every stated requirement", "factual claims", "format or schema",
            "confirm scope before executing", "every named acceptance criterion",
            "requested output must appear", "reading back the exact target",
            "Do NOT re-verify internal file edits", "Declared totals",
            "re-fetch or parse programmatically", "set fields explicitly",
            "Preserve identifiers, commands, and values exactly as given",
            "validate format first", "do NOT guess or hallucinate",
            "information cannot be retrieved by tools", "label assumptions explicitly",
        )),
    ],
)
def test_guidance_retains_action_and_safety_obligations(guidance, obligations):
    # These are instructions delivered to the model, not Python source checks.
    for obligation in obligations:
        assert obligation in guidance


@pytest.mark.parametrize("tools", [None, {"terminal", "web_search"}, {"terminal"}])
def test_execution_guidance_toolset_filter_keeps_safety_contract(tools):
    rendered = pb.execution_guidance_text(tools)
    assert rendered == pb.execution_guidance_text(tools)
    for section in ("verification", "external_state_verification",
                    "literal_preservation", "missing_context"):
        assert f"<{section}>" in rendered
        assert f"</{section}>" in rendered
    assert "Arithmetic, math, calculations → use terminal or execute_code" in rendered
    assert "Your memory and user profile describe the USER" in rendered
    if tools is not None and "web_search" not in tools:
        assert "web_search" not in rendered
        assert "(search_files, read_file, etc.)" in rendered
    else:
        assert "Current facts (weather, news, versions) → use web_search" in rendered
