"""Tests: synthetic PDFs always; the real official documents when you have them.

    pytest                                    # synthetic tests
    SYLLABUS_PDFS=/path/to/pdfs pytest        # also checks the real SAT, ACT, AP and Alberta documents

Layout of SYLLABUS_PDFS: sat/framework.pdf, act/{English,Math,Reading,Science}.pdf,
ap/calculus.pdf, ap/physics-1.pdf, alberta/physics20-30.pdf.
"""

import json
import os
from pathlib import Path

import pymupdf
import pytest

from syllabus_parsers import cli, parse_act, parse_alberta, parse_ap, parse_sat
from syllabus_parsers.sat import _clean, _expand

PDFS = Path(os.environ["SYLLABUS_PDFS"]) if os.environ.get("SYLLABUS_PDFS") else None
real = pytest.mark.skipif(PDFS is None, reason="set SYLLABUS_PDFS to a folder of the official PDFs")


# ---- synthetic -------------------------------------------------------------------

def _act_math_pdf(folder: Path) -> Path:
    """A one-page stand-in for ACT's Math standards: coded standards in text blocks."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    lines = [
        (72, "N 201. Perform one-operation computation with whole numbers and decimals"),
        (100, "N 202. Recognize equivalent fractions and fractions in lowest terms"),
        (128, "N 705. Multiply matrices"),
        (156, "A 301. Substitute whole numbers for unknown quantities to evaluate expressions"),
    ]
    for y, text in lines:
        page.insert_textbox(pymupdf.Rect(60, y, 560, y + 26), text, fontsize=10)
    page.insert_textbox(pymupdf.Rect(60, 400, 560, 430), "SCORE RANGE", fontsize=10)  # page furniture
    path = folder / "Math.pdf"
    doc.save(path)
    return path


def test_act_codes_become_objectives_under_score_ranges(tmp_path):
    _act_math_pdf(tmp_path)
    [math] = parse_act(tmp_path)
    assert (math.subject_id, math.level) == ("ACTM", "ACT")
    by_id = {o.lo_id: o for o in math.objectives}
    assert by_id["ACTM-1.705"].title == "Multiply matrices"
    assert by_id["ACTM-1.705"].topic_name == "Number and Quantity (ACT score 33–36)"
    assert by_id["ACTM-2.301"].include == ("A 301: Substitute whole numbers for unknown quantities to evaluate expressions",)
    assert not any("SCORE" in o.title for o in math.objectives)


def test_cli_writes_json(tmp_path):
    _act_math_pdf(tmp_path)
    out = tmp_path / "act.json"
    assert cli.main(["act", str(tmp_path), "-o", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    ids = [o["lo_id"] for t in data["subjects"][0]["topics"] for o in t["learning_objectives"]]
    assert "ACTM-1.705" in ids


def test_sat_cleanup_keeps_exponents_and_punctuation():
    assert _clean("changes all areas by a factor of k ^2 , and volumes by k ^3 .") == \
        "changes all areas by a factor of k^2, and volumes by k^3."


def test_sat_bullets_become_one_testing_point_each():
    statement = {"text": "Solve problems in a variety of contexts using:",
                 "bullets": [{"text": "the Pythagorean theorem.", "subs": []},
                             {"text": "right triangle trigonometry.", "subs": []}]}
    assert _expand(statement) == ["Solve problems in a variety of contexts using: the Pythagorean theorem.",
                                  "Solve problems in a variety of contexts using: right triangle trigonometry."]


# ---- the real documents --------------------------------------------------------------

@real
def test_real_sat_framework():
    subjects = {s.subject_id: s for s in parse_sat(PDFS / "sat" / "framework.pdf")}
    assert [len(subjects[k].objectives) for k in ("SATRW", "SATM", "PSAT89M")] == [10, 19, 17]
    left_out = {o.lo_id: o for o in subjects["PSAT89M"].objectives}["PSAT89M-X"].exclude
    assert "Circles (SAT and PSAT/NMSQT only, not PSAT 8/9)" in left_out


@real
def test_real_act_standards():
    subjects = parse_act(PDFS / "act")
    assert sum(len(s.objectives) for s in subjects) == 456
    math = next(s for s in subjects if s.subject_id == "ACTM")
    assert {o.lo_id: o.title for o in math.objectives}["ACTM-1.705"] == "Multiply matrices"


@real
def test_real_ap_calculus_ab_excludes_bc_only_content():
    ab, bc = parse_ap(PDFS / "ap" / "calculus.pdf", code="CALC", name="Calculus", calculus=True)
    ab_excluded = [e for o in ab.objectives for e in o.exclude]
    assert "Ratio Test for Convergence (topic 10.8, BC only)" in ab_excluded
    assert any(o.title == "Ratio Test for Convergence" for o in bc.objectives)


@real
def test_real_ap_physics_1():
    [phys] = parse_ap(PDFS / "ap" / "physics-1.pdf", code="PHYS1", name="Physics 1")
    assert len(phys.objectives) == 43


@real
def test_real_alberta_physics_30():
    subject = parse_alberta(PDFS / "alberta" / "physics20-30.pdf", course="Physics 30", code="PHYS30")
    assert len(subject.objectives) == 10
    assert any("photoelectric" in " ".join(o.include).lower() for o in subject.objectives)
