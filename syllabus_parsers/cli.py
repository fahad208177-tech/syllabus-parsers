"""Command line: official syllabus PDF in, JSON out.

    syllabus-parse sat framework.pdf -o sat.json
    syllabus-parse act ./act-pdfs/ -o act.json
    syllabus-parse ap calculus.pdf --code CALC --name Calculus --calculus -o calc.json
    syllabus-parse ap physics-1.pdf --code PHYS1 --name "Physics 1"
    syllabus-parse alberta physics20-30.pdf --course "Physics 30" --code PHYS30
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, parse_act, parse_alberta, parse_ap, parse_sat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="syllabus-parse", description="Official exam syllabus PDFs to structured JSON.")
    parser.add_argument("--version", action="version", version=f"syllabus-parsers {__version__}")
    sub = parser.add_subparsers(dest="exam", required=True)

    sat = sub.add_parser("sat", help="Digital SAT Suite assessment framework PDF")
    sat.add_argument("pdf")
    act = sub.add_parser("act", help="folder with ACT CCRS English/Math/Reading/Science PDFs")
    act.add_argument("folder")
    ap = sub.add_parser("ap", help="an AP Course and Exam Description PDF")
    ap.add_argument("pdf")
    ap.add_argument("--code", required=True, help="subject code, e.g. PHYS1")
    ap.add_argument("--name", required=True, help='course name, e.g. "Physics 1"')
    ap.add_argument("--calculus", action="store_true", help="split the Calculus CED into AB and BC")
    ab = sub.add_parser("alberta", help="an Alberta Education Program of Studies PDF")
    ab.add_argument("pdf")
    ab.add_argument("--course", required=True, help='as printed in the document, e.g. "Physics 30"')
    ab.add_argument("--code", required=True)
    ab.add_argument("--name")
    for p in (sat, act, ap, ab):
        p.add_argument("-o", "--output", help="write JSON here instead of stdout")

    args = parser.parse_args(argv)
    if args.exam == "sat":
        subjects = parse_sat(args.pdf)
    elif args.exam == "act":
        subjects = parse_act(args.folder)
    elif args.exam == "ap":
        subjects = parse_ap(args.pdf, code=args.code, name=args.name, calculus=args.calculus)
    else:
        subjects = [parse_alberta(args.pdf, course=args.course, code=args.code, name=args.name)]

    text = json.dumps({"subjects": [s.to_dict() for s in subjects]}, indent=1, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    for s in subjects:
        excluded = sum(len(o.exclude) for o in s.objectives)
        print(f"{s.level} {s.name} ({s.code}): {len(s.topics)} topics, {len(s.objectives)} objectives, "
              f"{excluded} exclusions", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
