"""Turn official exam syllabus PDFs into structured, citable learning objectives.

    from syllabus_parsers import parse_sat, parse_act, parse_ap, parse_alberta

    for subject in parse_sat("assessment-framework-for-digital-sat-suite.pdf"):
        for objective in subject.objectives:
            print(objective.lo_id, objective.title, objective.exclude)

Every function returns :class:`~syllabus_parsers.schema.Subject` objects
(subject -> topics -> learning objectives); ``Subject.to_dict()`` gives JSON.
"""

from __future__ import annotations

from pathlib import Path

from .schema import LearningObjective, Subject, Topic

__version__ = "0.1.0"
__all__ = ["parse_sat", "parse_act", "parse_ap", "parse_alberta", "Subject", "Topic", "LearningObjective"]


def parse_sat(pdf: str | Path) -> list[Subject]:
    """Digital SAT Suite assessment framework -> SAT Reading and Writing, SAT Math, PSAT 8/9 Math.

    PSAT 8/9 Math records the SAT content it leaves out as exclusions.
    """
    from .sat import parse

    return parse(pdf)


def parse_act(folder: str | Path) -> list[Subject]:
    """ACT College and Career Readiness Standards -> ACT English, Math, Reading, Science.

    ``folder`` holds any of English.pdf, Math.pdf, Reading.pdf, Science.pdf
    (ACT's CCRS-*Standards.pdf files, renamed). Each coded standard
    ("N 705. Multiply matrices") becomes an objective under its strand and
    score range.
    """
    from .act import parse

    return parse(folder)


def parse_ap(pdf: str | Path, *, code: str, name: str, calculus: bool = False) -> list[Subject]:
    """An AP Course and Exam Description -> one subject (or AB and BC for Calculus).

    With ``calculus=True`` the Calculus CED becomes two subjects: Calculus AB,
    where content marked "bc only" is recorded as excluded, and Calculus BC.
    """
    from .ap import parse_ced, to_subject

    topics = parse_ced(pdf)
    if calculus:
        return [to_subject(topics, code=f"{code}AB", name=f"{name} AB", source=f"AP {name} CED", bc_handling="exclude"),
                to_subject(parse_ced(pdf), code=f"{code}BC", name=f"{name} BC", source=f"AP {name} CED")]
    return [to_subject(topics, code=code, name=name, source=f"AP {name} CED")]


def parse_alberta(pdf: str | Path, *, course: str, code: str, name: str | None = None) -> Subject:
    """An Alberta Education Program of Studies -> the 30-level (Diploma) course's outcomes.

    ``course`` is the course as printed in the document, e.g. "Physics 30".
    """
    from .alberta import parse

    name = name or course
    return parse(pdf, course=course, code=code, name=name, source=f"Alberta {name} Program of Studies")
