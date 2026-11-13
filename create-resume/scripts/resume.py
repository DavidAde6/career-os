#!/usr/bin/env python3
"""Catalog a Jake-style master resume and render only permitted selections."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unicodedata
from check_layout import check


def require(condition, message):
    if not condition:
        raise ValueError(message)


def escaped(text, pos):
    backslashes = 0
    while pos > 0 and text[pos - 1] == "\\":
        pos -= 1
        backslashes += 1
    return backslashes % 2 == 1


def uncomment(text):
    return "\n".join(re.split(r"(?<!\\)%", line, maxsplit=1)[0]
                     for line in text.splitlines())


def arguments(text, pos, count):
    result = []
    for _ in range(count):
        while pos < len(text):
            if text[pos].isspace():
                pos += 1
            elif text[pos] == "%" and not escaped(text, pos):
                end = text.find("\n", pos)
                pos = len(text) if end == -1 else end + 1
            else:
                break
        require(pos < len(text) and text[pos] == "{", "Unsupported macro arguments")
        start, depth = pos + 1, 1
        pos += 1
        while pos < len(text) and depth:
            char = text[pos]
            if char == "%" and not escaped(text, pos):
                end = text.find("\n", pos)
                pos = len(text) if end == -1 else end + 1
                continue
            if char in "{}" and not escaped(text, pos):
                depth += 1 if char == "{" else -1
            pos += 1
        require(depth == 0, "Unbalanced LaTeX braces")
        result.append((start, pos - 1, text[start:pos - 1]))
    return result


def commands(text, name):
    for match in re.finditer(r"\\" + re.escape(name) + r"\b", text):
        line = text[text.rfind("\n", 0, match.start()) + 1:match.start()]
        if uncomment(line) == line:
            yield match


def splice(text, edits):
    last_start = len(text)
    for start, end, value in sorted(edits, reverse=True):
        require(0 <= start <= end <= last_start, "Overlapping source edits")
        text = text[:start] + value + text[end:]
        last_start = start
    return text


def skill_lines(text):
    lines = []
    pattern = r"(?m)^[ \t]*\\textbf\{([^{}]+)\}\{: ([^{}]+)\}[^\n]*(?:\n|$)"
    for match in re.finditer(pattern, text):
        lines.append({"category": match[1], "tokens": match[2].split(", "),
                      "start": match.start(), "end": match.end(),
                      "category_start": match.start(1), "category_end": match.end(1),
                      "values_start": match.start(2), "values_end": match.end(2)})
    require(lines, "Unsupported Technical Skills structure")
    require(len({line["category"] for line in lines}) == len(lines),
            "Duplicate skill category")
    return lines


def parse(text):
    document = text.index(r"\begin{document}")
    sections = list(commands(text[document:], "section"))
    entries = []
    technical = None
    for index, section in enumerate(sections):
        start = document + section.start()
        end = document + sections[index + 1].start() if index + 1 < len(sections) else text.index(r"\end{document}")
        label = arguments(text, document + section.end(), 1)[0][2]
        if label == "Technical Skills":
            technical = (start, end, skill_lines(text[start:end]))
            continue
        require(label in {"Experience", "Projects", "Education"},
                f"Unsupported master section: {label}")
        section_text = text[start:end]
        macro = "resumeProjectHeading" if label == "Projects" else "resumeSubheading"
        matches = list(commands(section_text, macro))
        require(matches, f"No supported entries in {label}")
        list_end = section_text.rfind(r"\resumeSubHeadingListEnd")
        require(list_end > matches[-1].start(), f"Missing list end in {label}")
        for n, match in enumerate(matches):
            a = start + match.start()
            b = start + (matches[n + 1].start() if n + 1 < len(matches) else list_end)
            args = arguments(text, start + match.end(), 2 if label == "Projects" else 4)
            block = text[a:b]
            bullets = []
            for bullet in commands(block, "resumeItem"):
                arg = arguments(block, bullet.end(), 1)[0]
                bullets.append({"start": a + bullet.start(), "end": a + arg[1] + 1,
                                "text": arg[2], "command": block[bullet.start():arg[1] + 1]})
            require(bullets, f"No bullets in {label} entry {n + 1}")
            item_starts = list(commands(block, "resumeItemListStart"))
            item_ends = list(commands(block, "resumeItemListEnd"))
            require(len(item_starts) == len(item_ends) == 1,
                    "Unsupported nested bullet-list structure")
            entries.append({"id": f"{label.lower()}-{n + 1}", "section": label,
                            "section_start": start, "section_end": end,
                            "start": a, "end": b, "args": args, "bullets": bullets,
                            "list_start": a + item_starts[0].start(),
                            "list_end": a + item_ends[0].end()})
    require(technical is not None, "Technical Skills section missing")
    skills = technical[2]
    for entry in entries:
        if entry["section"] != "Projects":
            continue
        heading = entry["args"][0]
        stacks = list(commands(heading[2], "emph"))
        require(len(stacks) == 1, "Expected exactly one project stack in emph")
        stack = arguments(text, heading[0] + stacks[0].end(), 1)[0]
        allowed = stack[2].split(", ")
        evidence = uncomment(text[entry["start"]:entry["end"]])
        for line in skills:
            for token in line["tokens"]:
                if token not in allowed and re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", evidence, re.I):
                    allowed.append(token)
        entry["stack"] = stack
        entry["allowed_stack"] = allowed
    return entries, technical


def source(path):
    raw = path.read_bytes()
    return raw, raw.decode("utf-8-sig").replace("\r\n", "\n")


def catalog(raw, text):
    entries, technical = parse(text)
    output = {"master_sha256": hashlib.sha256(raw).hexdigest(), "entries": [],
              "skills": {line["category"]: line["tokens"] for line in technical[2]}}
    for entry in entries:
        item = {"id": entry["id"], "heading_arguments": [arg[2] for arg in entry["args"]],
                "bullets": {str(n): b["text"] for n, b in enumerate(entry["bullets"], 1)}}
        if "allowed_stack" in entry:
            item["allowed_stack"] = entry["allowed_stack"]
        output["entries"].append(item)
    return output


def subset(values, allowed, label, nonempty=True):
    require(isinstance(values, list) and (values or not nonempty), f"{label}: expected a list")
    require(all(isinstance(v, str) for v in values), f"{label}: expected strings")
    require(len(values) == len(set(values)) and set(values) <= set(allowed),
            f"{label}: duplicate or unsupported tokens")


def latex_text(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in value)


def render(raw, text, selection):
    require(isinstance(selection, dict), "Selection must be an object")
    require(set(selection) == {"master_sha256", "company", "role", "entries", "skills"},
            "Selection requires only master_sha256, company, role, entries, and skills")
    require(selection["master_sha256"] == hashlib.sha256(raw).hexdigest(),
            "Master changed; regenerate the catalog and selection")
    entries, technical = parse(text)
    choices = selection["entries"]
    require(isinstance(choices, dict) and set(choices) <= {e["id"] for e in entries},
            "Unknown entry ID")
    edits, expected = [], Counter()
    omitted_sections = set()
    for entry in entries:
        label = entry["section"]
        if label != "Education" and not any(e["id"] in choices for e in entries if e["section"] == label):
            if label not in omitted_sections:
                edits.append((entry["section_start"], entry["section_end"], ""))
                omitted_sections.add(label)
    for entry in entries:
        if entry["section"] in omitted_sections:
            continue
        choice = choices.get(entry["id"])
        if choice is None:
            require(entry["section"] != "Education", "Education metadata must be retained")
            edits.append((entry["start"], entry["end"], ""))
            continue
        allowed_fields = {"bullets", "title"} if entry["section"] == "Experience" else {"bullets", "stack"} if entry["section"] == "Projects" else {"bullets"}
        require(isinstance(choice, dict) and "bullets" in choice and set(choice) <= allowed_fields,
                f"Unsupported fields for {entry['id']}")
        numbers = choice["bullets"]
        require(isinstance(numbers, list) and all(type(n) is int for n in numbers),
                "Bullet numbers must be a list of integers")
        require(len(numbers) == len(set(numbers)) and all(1 <= n <= len(entry["bullets"]) for n in numbers),
                f"Invalid or duplicate bullet index for {entry['id']}")
        require(numbers or entry["section"] == "Education", "Retained work/project needs a bullet")
        selected = [entry["bullets"][n - 1] for n in numbers]
        expected.update(b["text"] for b in selected)
        for index, bullet in enumerate(entry["bullets"]):
            value = selected[index]["command"] if index < len(selected) else ""
            edits.append((bullet["start"], bullet["end"], value))
        if not numbers:
            edits = [edit for edit in edits if not (entry["list_start"] <= edit[0] < entry["list_end"])]
            edits.append((entry["list_start"], entry["list_end"], ""))
        if "title" in choice:
            title = choice["title"]
            require(isinstance(title, str) and title.strip() and not any(ord(c) < 32 for c in title),
                    "Title must be nonempty plain text on one line")
            original = entry["args"][0]
            require("intern" not in original[2].lower() or re.search(r"\bintern\b", title, re.I),
                    "Cannot remove internship status")
            edits.append((original[0], original[1], latex_text(title)))
        if "stack" in choice:
            subset(choice["stack"], entry["allowed_stack"], "Project stack")
            stack = entry["stack"]
            edits.append((stack[0], stack[1], ", ".join(choice["stack"])))
    skills = selection["skills"]
    require(isinstance(skills, dict) and skills, "Select at least one skill category")
    section_start, _, lines = technical
    allowed_tokens = {token for line in lines for token in line["tokens"]}
    rendered_lines, used_tokens = [], set()
    # Categories are editorial labels; factual skill tokens still come only from the master.
    line = lines[0]
    original = text[section_start + line["start"]:section_start + line["end"]]
    for category, tokens in skills.items():
        require(isinstance(category, str) and category.strip() == category and category
                and not any(ord(c) < 32 for c in category),
                "Skill category must be nonempty plain text on one line")
        subset(tokens, allowed_tokens, category)
        require(not used_tokens.intersection(tokens), "Duplicate skill tokens across categories")
        used_tokens.update(tokens)
        rendered_lines.append(splice(original, [(line["category_start"] - line["start"],
                                                line["category_end"] - line["start"], latex_text(category)),
                                               (line["values_start"] - line["start"],
                                                line["values_end"] - line["start"], ", ".join(tokens))]))
    for index, line in enumerate(lines):
        value = rendered_lines[index] if index < len(rendered_lines) else ""
        if index == len(lines) - 1:
            value += "".join(rendered_lines[len(lines):])
        edits.append((section_start + line["start"], section_start + line["end"],
                      value))
    output = splice(text, edits)
    # Inspect actual output commands to verify verbatim bullet provenance.
    body = output[output.index(r"\begin{document}"):]
    actual = Counter(arguments(body, match.end(), 1)[0][2] for match in commands(body, "resumeItem"))
    require(actual == expected, "Rendered bullets do not match selected master bullets")
    return output


def safe_component(value):
    require(isinstance(value, str) and value.strip(), "Company and role must be nonempty strings")
    value = unicodedata.normalize("NFKC", value).strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", "-", value).strip(" .-_")[:70].rstrip(" .-_")
    require(value and value not in {".", ".."}, "Company/role has no usable filename characters")
    return value


def publish(directory, stem, text, pdf):
    """Reserve a versioned folder and deliver only the source and validated PDF."""
    require(pdf.is_file(), "Validated PDF is missing")
    directory.mkdir(parents=True, exist_ok=True)
    # Count both new folders and legacy loose files to preserve prior iterations.
    pattern = re.compile(re.escape(stem) + r"(?:_(\d+))?(?:\.(?:tex|pdf))?", re.I)
    for _ in range(100):
        versions = [int(m[1] or 1) for p in directory.iterdir() if (m := pattern.fullmatch(p.name))]
        version = max(versions, default=0) + 1
        name = stem + (f"_{version}" if version > 1 else "")
        folder = directory / name
        try:
            folder.mkdir()
        except FileExistsError:
            continue
        path = folder / (name + ".tex")
        pdf_path = folder / (name + ".pdf")
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            with pdf.open("rb") as source_pdf, pdf_path.open("xb") as target_pdf:
                shutil.copyfileobj(source_pdf, target_pdf)
            return path
        except BaseException:
            # Remove only files in the folder reserved by this invocation.
            path.unlink(missing_ok=True)
            pdf_path.unlink(missing_ok=True)
            folder.rmdir()
            raise
    raise ValueError("Could not reserve a resume version after concurrent writes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["catalog", "render"])
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--underfill-reason", help="Explain why no additional relevant content can fit; never used to bypass overflow checks")
    args = parser.parse_args()
    try:
        master = args.master.resolve(strict=True)
        raw, text = source(master)
        if args.command == "catalog":
            print(json.dumps(catalog(raw, text), ensure_ascii=True, indent=2))
            return
        require(args.selection is not None, "render requires --selection")
        selection = json.loads(args.selection.read_text(encoding="utf-8-sig"))
        output = render(raw, text, selection)
        stem = safe_component(selection["company"]) + "_" + safe_component(selection["role"])
        require(master.read_bytes() == raw, "Master changed during rendering; regenerate selection")
        if args.publish:
            directory = Path(tempfile.mkdtemp(prefix="create-resume-publish-"))
            candidate = directory / (stem + ".tex")
            candidate.write_text(output, encoding="utf-8", newline="\n")
            validation = check(candidate, master)
            require(validation["layout_verified"],
                    "Layout validation failed; revise the selection before publication: " + json.dumps(validation))
            require(validation["fill_target_met"] or (args.underfill_reason and args.underfill_reason.strip()),
                    "Page is underfilled; add relevant master content and recompile, or explain why none can fit with --underfill-reason: " + json.dumps(validation))
            if not validation["fill_target_met"]:
                validation["underfill_reason"] = args.underfill_reason.strip()
            require(master.read_bytes() == raw, "Master changed during validation; regenerate selection")
            path = publish(master.parent / "resumes", stem, output, Path(validation["pdf"]))
        else:
            directory = Path(tempfile.mkdtemp(prefix="create-resume-"))
            path = directory / (stem + ".tex")
            path.write_text(output, encoding="utf-8", newline="\n")
        print(json.dumps({"path": str(path), "published": args.publish,
                          "layout_verified": args.publish,
                          **({"pdf": str(path.with_suffix(".pdf")),
                              "directory": str(path.parent),
                              "validation": validation} if args.publish else {})}, ensure_ascii=True))
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
