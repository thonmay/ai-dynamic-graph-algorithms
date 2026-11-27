# AI-assisted code: generated and revised with Gemini 4 Hydrogen
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for Lean comment scanning in evoalgo.formalize."""

from evoalgo.formalize import _has_theorem, _scan_for_banned


def test_scan_for_banned_inline_and_multiline_comments(tmp_path):
    p = tmp_path / "Test.lean"
    p.write_text(
        "/- ok -/ sorry\n"
        "theorem t1 : True := by\n"
        "  /- outer /- inner sorry -/ still comment sorry -/\n"
        "  trivial -- sorry\n"
        "def bad := /- block\n"
        "  sorry\n"
        "-/ admit\n"
    )
    assert _has_theorem(p) is True
    hits = _scan_for_banned(p)
    assert hits == ["1: sorry", "7: admit"], hits


def test_has_theorem_ignores_commented_theorem(tmp_path):
    p = tmp_path / "NoThm.lean"
    p.write_text(
        "/- theorem fake : True := trivial -/\n"
        "-- theorem also_fake : True := trivial\n"
        "def x := 1\n"
    )
    assert _has_theorem(p) is False
    assert _scan_for_banned(p) == []
