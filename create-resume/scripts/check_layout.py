#!/usr/bin/env python3
"""Compile a temporary PDF and check one-page fit using pdfLaTeX/MiKTeX."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def measure_fill(compiler, pdf, build, probe_log):
    """Compare the last visible word with the live template's body bottom."""
    extractor = Path(compiler).parent / ("pdftotext.exe" if os.name == "nt" else "pdftotext")
    if not extractor.is_file():
        extractor = shutil.which("pdftotext")
    if not extractor:
        raise ValueError("pdftotext is required to measure page utilization; MiKTeX supplies it beside pdflatex.")
    bbox = build / "text-bounds.html"
    subprocess.run([str(extractor), "-bbox", str(pdf), str(bbox)], check=True,
                   capture_output=True, timeout=30)
    document = ET.parse(bbox)
    pages = [e for e in document.iter() if e.tag.split("}")[-1] == "page"]
    if len(pages) != 1:
        return {"fill_target_met": False, "unused_height_pt": None}
    words = [e for e in pages[0].iter() if e.tag.split("}")[-1] == "word" and (e.text or "").strip()]
    if not words:
        raise ValueError("Cannot measure page utilization: PDF has no extractable words.")
    bottom_match = re.search(r"RESUME-TEXT-BOTTOM:([\d.]+)pt", probe_log)
    top_match = re.search(r"RESUME-TEXT-TOP:([\d.]+)pt", probe_log)
    if not bottom_match or not top_match:
        raise ValueError("Cannot measure the template's text area.")
    # TeX points use 72.27/in; PDF coordinates use 72/in.
    body_bottom = float(bottom_match[1]) * 72 / 72.27
    body_top = float(top_match[1]) * 72 / 72.27
    content_bottom = max(float(word.attrib["yMax"]) for word in words)
    unused = max(0, body_bottom - content_bottom)
    config = Path(__file__).resolve().parents[1] / "references/layout.json"
    limit = json.loads(config.read_text(encoding="utf-8"))["max_unused_height_pt"]
    if not isinstance(limit, (int, float)) or not 0 <= limit <= 72:
        raise ValueError("max_unused_height_pt must be between 0 and 72 PDF points.")
    return {"body_bottom_pt": round(body_bottom, 1), "content_bottom_pt": round(content_bottom, 1),
            "unused_height_pt": round(unused, 1), "max_unused_height_pt": limit,
            "body_used_percent": round(100 * (content_bottom - body_top) / (body_bottom - body_top), 1),
            "fill_target_met": unused <= limit}


def find_compiler(override=None):
    candidates = [override] if override else [shutil.which("pdflatex")]
    if not override:
        for root in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles")):
            if root:
                base = Path(root)
                if root == os.environ.get("LOCALAPPDATA"):
                    base /= "Programs"
                candidates.append(base / "MiKTeX/miktex/bin/x64/pdflatex.exe")
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise ValueError("pdfLaTeX not found. Install MiKTeX or pass --compiler with the executable path.")


def compile_tex(compiler, tex, build, cwd, job):
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20)
    miktex = "MiKTeX" in version.stdout
    flags = ["-disable-write18", "-enable-installer"] if miktex else ["-no-shell-escape"]
    command = [compiler, *flags, "-interaction=nonstopmode", "-halt-on-error",
               "-file-line-error", f"-output-directory={build}", f"-jobname={job}", str(tex)]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=300)
    log_file = build / f"{job}.log"
    log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
    if result.returncode:
        raise ValueError(f"pdfLaTeX failed; build files: {build}\n" +
                         (result.stdout + result.stderr)[-5000:])
    matches = re.findall(r"Output written on .*?\((\d+) pages?,", log, re.S)
    if not matches or not (build / f"{job}.pdf").is_file():
        raise ValueError(f"Cannot establish PDF page count; inspect {log_file}")
    return int(matches[-1]), log


def check(tex, master, compiler=None):
    tex, master = Path(tex).resolve(strict=True), Path(master).resolve(strict=True)
    compiler = find_compiler(compiler)
    source_bytes, master_bytes = tex.read_bytes(), master.read_bytes()
    build = Path(tempfile.mkdtemp(prefix="create-resume-build-"))
    # Use a byte-identical copy for compilation; never write alongside the master.
    exact = build / "candidate.tex"
    exact.write_bytes(source_bytes)
    pages, log = compile_tex(compiler, exact, build, master.parent, "resume-check")
    overfull = re.findall(r"Overfull \\[hv]box[^\n]*", log)
    text = source_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    heading_count = len(re.findall(r"(?m)^[ \t]*\\resumeProjectHeading\b", text))
    overflow_count = 0
    instrumented = text
    if heading_count:
        # The probe changes no visible output and exists only in the build directory.
        pattern = r"(\\newcommand\{\\resumeProjectHeading\}\[2\]\{)"
        probe = (r"\begingroup\setbox0=\hbox{\small#1\hspace{2\tabcolsep}#2}"
                 r"\typeout{RESUME-PROJECT-MEASURED}"
                 r"\ifdim\wd0>0.97\textwidth\typeout{RESUME-PROJECT-OVERFLOW}\fi\endgroup")
        instrumented, count = re.subn(pattern, lambda m: m[1] + "\n" + probe, text)
        if count != 1:
            raise ValueError("Project-heading macro changed; adapt the width probe before validating.")
    # Measure complete skills rows inside the existing itemize context, where linewidth
    # includes the template's list indentation. Long rows can wrap without an overfull box.
    skills_start = instrumented.index(r"\section{Technical Skills}")
    skills_prefix, skills_body = instrumented[:skills_start], instrumented[skills_start:]
    skill_count = 0

    def skill_probe(match):
        nonlocal skill_count
        skill_count += 1
        row = re.sub(r"\\\\\s*$", "", match[0]).strip()
        probe = (r"\begingroup\setbox0=\hbox{\small " + row + "}"
                 + rf"\typeout{{RESUME-SKILL-MEASURED:{skill_count}:\the\wd0:\the\linewidth}}"
                 + r"\ifdim\wd0>\linewidth\typeout{RESUME-SKILL-OVERFLOW}\fi\endgroup")
        return probe + "\n" + match[0]

    skills_body = re.sub(r"(?m)^[ \t]*\\textbf\{[^\n]+", skill_probe, skills_body)
    if not skill_count:
        raise ValueError("No skills rows found; adapt the width probe before validating.")
    instrumented = skills_prefix + skills_body
    dimensions = (r"\typeout{RESUME-TEXT-TOP:\the\dimexpr1in+\voffset+\topmargin+\headheight+\headsep\relax}"
                  r"\typeout{RESUME-TEXT-BOTTOM:\the\dimexpr1in+\voffset+\topmargin+\headheight+\headsep+\textheight\relax}")
    instrumented = instrumented.replace(r"\begin{document}", dimensions + "\n" + r"\begin{document}", 1)
    probe_tex = build / "heading-probe.tex"
    probe_tex.write_text(instrumented, encoding="utf-8", newline="\n")
    probe_pages, probe_log = compile_tex(compiler, probe_tex, build, master.parent, "heading-probe")
    if probe_log.count("RESUME-PROJECT-MEASURED") != heading_count or probe_pages != pages:
        raise ValueError("Measurement did not cover every heading or changed pagination.")
    overflow_count = probe_log.count("RESUME-PROJECT-OVERFLOW")
    skill_overflows = probe_log.count("RESUME-SKILL-OVERFLOW")
    measurements = re.findall(r"RESUME-SKILL-MEASURED:(\d+):([\d.]+)pt:([\d.]+)pt", probe_log)
    if len(measurements) != skill_count:
        raise ValueError("Measurement did not cover every skills row.")
    skill_widths = [{"row": int(row), "width_pt": round(float(width), 1),
                     "available_width_pt": round(float(limit), 1),
                     "used_percent": round(100 * float(width) / float(limit), 1)}
                    for row, width, limit in measurements]
    fill = measure_fill(compiler, build / "resume-check.pdf", build, probe_log)
    if tex.read_bytes() != source_bytes or master.read_bytes() != master_bytes:
        raise ValueError("Source or master changed during validation; rerun on the latest candidate.")
    return {"compiler": compiler, "pages": pages, "project_headings": heading_count,
            "project_heading_overflows": overflow_count, "overfull_boxes": overfull,
            "skill_rows": skill_count, "skill_row_overflows": skill_overflows,
            "skill_row_measurements": skill_widths,
            "layout_verified": pages == 1 and not overflow_count and not skill_overflows and not overfull,
            **fill,
            "publication_ready": pages == 1 and not overflow_count and not skill_overflows and not overfull and fill["fill_target_met"],
            "pdf": str(build / "resume-check.pdf"), "build_directory": str(build),
            "visual_review": "Inspect the temporary PDF for glyphs, overlap, and clipping."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--compiler")
    args = parser.parse_args()
    try:
        result = check(args.tex, args.master, args.compiler)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["publication_ready"] else 1)
    except (ValueError, OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError, ET.ParseError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
