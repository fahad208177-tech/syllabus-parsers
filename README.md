# syllabus-parsers

**Turn official exam syllabus PDFs into structured, citable learning objectives.**

Every study app, tutor and revision tool eventually needs the same thing: what is
actually on the exam, in the exam board's own words, with what's explicitly *not*
assessed. That information exists only in long PDFs written for humans. Their
layouts beat generic PDF-to-text tools: tables whose columns run together,
codes in three different formats, bullets nested by indentation, formulas
broken into separate characters.

`syllabus-parsers` reads the official documents and gives you clean data:

```json
{
  "lo_id": "ACTM-1.705",
  "title": "Multiply matrices",
  "include": ["N 705: Multiply matrices"],
  "exclude": [],
  "source": "ACT College and Career Readiness Standards",
  "page": 2
}
```

It was built for [Syllabuddy](https://github.com/fahad208177-tech/Syllabuddy), an
Alexa+ add-on that answers "is this on my exam?", and released on its own so
anyone can use the data.

## Supported documents

| Exam | Document | Output |
|---|---|---|
| **Digital SAT Suite** | [Assessment Framework for the Digital SAT Suite](https://satsuite.collegeboard.org/media/pdf/assessment-framework-for-digital-sat-suite.pdf) (College Board) | SAT Reading and Writing (10 skills), SAT Math (19 skills, 112 testing points), PSAT 8/9 Math (17 skills, with 33 exclusions: SAT content the PSAT 8/9 leaves out) |
| **ACT** | College and Career Readiness Standards: [English](https://www.act.org/content/dam/act/unsecured/documents/CCRS-EnglishStandards.pdf), [Math](https://www.act.org/content/dam/act/unsecured/documents/CCRS-MathStandards.pdf), [Reading](https://www.act.org/content/dam/act/unsecured/documents/CCRS-ReadingStandards.pdf), [Science](https://www.act.org/content/dam/act/unsecured/documents/CCRS-ScienceStandards.pdf) | 456 coded standards, each an objective under its strand and score range ("Number and Quantity (ACT score 33–36)") |
| **AP** | Any AP Course and Exam Description (CED) from [AP Central](https://apcentral.collegeboard.org/courses), tested on 22 courses plus Calculus | Units, topics and learning objectives with essential knowledge, exclusion statements and boundary statements. Calculus splits into AB and BC, with "bc only" content recorded as excluded from AB. |
| **Alberta Diploma** | Programs of Study, e.g. [Physics 20–30](https://education.alberta.ca/media/159713/phy2030_07.pdf), [Chemistry 20–30](https://education.alberta.ca/media/159730/chem2030_07.pdf) | 30-level general outcomes with their knowledge outcomes |

The PDFs are copyrighted by their publishers and are not included. Download
them yourself from the links above.

## Install

```bash
pip install git+https://github.com/fahad208177-tech/syllabus-parsers.git
```

Python 3.10+. The only dependency is [PyMuPDF](https://pymupdf.readthedocs.io/).

## Use

Command line (JSON to stdout, or `-o file.json`; a summary goes to stderr):

```bash
syllabus-parse sat assessment-framework-for-digital-sat-suite.pdf -o sat.json
syllabus-parse act ./act/ -o act.json        # folder with English.pdf, Math.pdf, Reading.pdf, Science.pdf
syllabus-parse ap calculus.pdf --code CALC --name Calculus --calculus -o calculus.json
syllabus-parse ap physics-1.pdf --code PHYS1 --name "Physics 1"
syllabus-parse alberta physics20-30.pdf --course "Physics 30" --code PHYS30
```

Python:

```python
from syllabus_parsers import parse_sat, parse_act, parse_ap, parse_alberta

for subject in parse_sat("assessment-framework-for-digital-sat-suite.pdf"):
    print(subject.name, len(subject.objectives))
    for objective in subject.objectives:
        print(" ", objective.lo_id, objective.title)
        for left_out in objective.exclude:
            print("    not assessed:", left_out)

ab, bc = parse_ap("calculus.pdf", code="CALC", name="Calculus", calculus=True)
```

## Output format

Every parser returns `Subject` objects (`subject.to_dict()` for JSON):

- **Subject**: `subject_id`, `name`, `code`, `level` (`"SAT"`, `"ACT"`, `"AP"`...), `source`, `topics`
- **Topic**: `topic_id`, `number`, `name`, `learning_objectives`
- **LearningObjective**:
  - `lo_id`: stable, citable id, e.g. `CALCBC-10.8`, `SATM-4.3`, `ACTM-1.705`
  - `title`, `statement`
  - `include`: the official wording of what is assessed
  - `exclude`: what the document says is *not* assessed, quoted
  - `keywords`, `exam_skills` (command words such as "calculate" and "explain")
  - `source`, `page`: where to check it

## How it works

These documents look simple and aren't. The parsers deal with:

- **Columns that vary by page.** AP CEDs mirror their layout on facing pages, so
  columns are found on each page from their headings. The SAT framework's
  three-column table (SAT, PSAT/NMSQT, PSAT 8/9) changes width from page to page,
  so column edges come from each page's most common left margins.
- **Text from neighbouring columns merged into one line.** PyMuPDF can join
  spans from different columns that share a baseline, so the SAT parser works
  span by span and regroups visual rows.
- **Nesting shown only by indentation.** Statements, bullets and sub-bullets are
  rebuilt from x-offsets, and each bullet becomes one testing point, prefixed
  with its stem.
- **Comparing exams.** The PSAT 8/9 column is compared with the SAT column bullet
  by bullet, so content the PSAT 8/9 leaves out becomes a PSAT 8/9 exclusion.
- **Three generations of AP codes** (`LIM-1.A`, `1.1.A`, `KC-4.1.IV.C`), "bc only"
  markers, exclusion and boundary statements, and AP CS Principles, which only
  groups topics in an at-a-glance table.
- **Debris:** page furniture, footers, alt text spelled out letter by letter,
  control characters used as spaces, and exponents (`k^2`) recovered from font
  size.

## Accuracy and limits

In Syllabuddy, all 2,883 objectives parsed by these and its other parsers are
checked automatically: no debris, every title found, every exclusion found. See
[its evaluation](https://github.com/fahad208177-tech/Syllabuddy#tests).

- Some formulas come out scrambled, because the PDFs place them glyph by glyph.
  This affects mostly AP Precalculus parametric and vector notation: the
  surrounding words are intact but the formula text reads oddly. Syllabuddy
  keeps hand-checked corrections for these; contributions welcome.
- Only the 30-level (Diploma) Alberta courses are parsed.
- Exam boards revise their documents. The parsers were built against the
  editions current in October 2026, and a new layout may need a fix.

## Tests

```bash
pip install -e ".[test]"
pytest                                    # synthetic PDFs, no downloads needed
SYLLABUS_PDFS=/path/to/pdfs pytest        # also the real SAT, ACT, AP and Alberta documents
```

`SYLLABUS_PDFS` holds `sat/framework.pdf`, `act/{English,Math,Reading,Science}.pdf`,
`ap/calculus.pdf`, `ap/physics-1.pdf` and `alberta/physics20-30.pdf`.

## License

MIT, for the code. The syllabus documents and their content belong to their
publishers (College Board, ACT, Alberta Education); this tool only reads copies
you have downloaded. SAT, PSAT/NMSQT, AP and ACT are trademarks of their owners,
who don't endorse this project.
