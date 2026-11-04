"""Behavioral prompt requirements retained from the old local lean-prompt tests."""
from pathlib import Path
import json

from agent import prompt_builder as pb


def test_narrow_skills_keep_safety_and_rendered_index(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    skill = tmp_path / 'skills' / 'specialist' / 'safe-work'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: safe-work\ndescription: Use before specialist actions.\n---\nConfirm writes.\n')
    pb.clear_skills_system_prompt_cache(clear_snapshot=True)
    try:
        rendered = pb.build_skills_system_prompt(available_tools={'terminal', 'skill_view'})
        for obligation in ('MUST load clearly applicable procedural skills', 'before specialist work or actions',
                           'domain safety', 'Casual conversation', 'tangential matches', 'safe-work',
                           'update it before finishing'):
            assert obligation in rendered
        assert 'even partially relevant' not in rendered
        assert 'Err on the side of loading' not in rendered
        assert 'web_search' not in rendered
    finally:
        pb.clear_skills_system_prompt_cache(clear_snapshot=True)


def test_lean_guidance_keeps_execution_safety_and_is_shorter_than_release():
    text = pb.execution_guidance_text()
    for obligation in ('every stated requirement', 'factual claims', 'format or schema',
                       'confirm scope before executing', 'every named acceptance criterion',
                       'requested output must appear', 'reading back the exact target',
                       'Declared totals', 're-fetch or parse programmatically', 'set fields explicitly',
                       'Preserve identifiers, commands, and values exactly as given',
                       'validate format first', 'do NOT guess or hallucinate', 'label assumptions explicitly'):
        assert obligation in text
    assert 'web_search' not in text  # Upstream tool-neutral improvement retained.
    names = ('TASK_COMPLETION_GUIDANCE', 'TOOL_USE_ENFORCEMENT_GUIDANCE',
             'PARALLEL_TOOL_CALL_GUIDANCE', 'OPENAI_MODEL_EXECUTION_GUIDANCE')
    baseline = Path(__file__).resolve().parents[2] / 'docs/upgrade/01/release-guidance.json'
    values = json.loads(baseline.read_text())
    assert sum(len(getattr(pb, n)) for n in names) < sum(len(values[n]) for n in names)
    assert 'working artifact' in pb.TASK_COMPLETION_GUIDANCE
    assert 'fabricated' in pb.TASK_COMPLETION_GUIDANCE
    assert 'same response' in pb.TOOL_USE_ENFORCEMENT_GUIDANCE
    assert 'Independent' in pb.PARALLEL_TOOL_CALL_GUIDANCE
