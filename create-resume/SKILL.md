---
name: create-resume
description: Create a tailored one-page resume as LaTeX and PDF from MasterResume.tex for a supplied company, role, and job description, selecting bullets verbatim and preserving the master layout.
---

# Create Resume

Generate `resumes/Company_Role/Company_Role.tex` and its matching `.pdf` from the project's live `MasterResume.tex`. The master is both the template and the sole factual source; never edit it. This skill lives in the project's `create-resume/` directory beside `resumes/`; resolve any directory link before taking its parent as the default project. Use another project's master only when explicitly requested. If the selected project lacks the master, ask for its location rather than using an unrelated resume.

Read [references/preferences.md](references/preferences.md) on every invocation. This is the editable home for selection priorities and title/skills preferences. The live master controls formatting; do not maintain a second template that can drift. Apply explicit invocation overrides, but ask before overriding a factual or source-preservation constraint.

## Inputs and evidence

Expect company, target role, and job description in the invocation. Ask for any missing required input. Read the entire master, including all alternate bullets. The posting supplies targeting criteria, never facts about the candidate. Do not import achievements from past tailored resumes, memory, company pages, or user answers. New factual information must first be added to the master through a separately authorized edit; this skill never changes the master.

Identify the posting's responsibilities, required/preferred qualifications, seniority, product/domain, and explicit values. Infer hiring emphasis from repeated requirements and concrete work; distinguish these inferences from stated requirements. Do not guess protected traits or unsupported company preferences. Use supplied material by default; research only when needed to resolve a material ambiguity or explicitly requested.

## Allowed changes

- Select and reorder whole existing bullet commands under their original role, project, or education entry. Copy their arguments exactly, including punctuation, metrics, LaTeX markup, and imperfect wording. Never splice, shorten, paraphrase, repair, duplicate, or move a bullet to another entry.
- Choose which experience/project entries to retain when necessary for relevance and fit; omit a section if no entries survive. Preserve retained employers, dates, locations, project names/links, education metadata, section sequence, and entry chronology.
- Change experience role titles using the preferences below, preserving actual seniority and employment type. The user permits software engineering equivalents for these roles, including `Software Engineering Intern - AI Platform`, `Software Engineering Intern - Agentic AI`, or neutral `Software Engineering Intern`. Match the target title when the master's responsibilities support it; do not turn an internship into a senior or permanent position.
- Trim/reorder project technology lists using technologies explicitly associated with that project in its heading or bullets. The entire heading (project name plus stack) must fit one rendered row. Do not shorten the project name to make room.
- Select/reorder technical skills using existing master skill tokens. Rename, merge, or split category labels to suit the role (for example, Backend, Full Stack, AI / ML, or Cloud / Tools), moving tokens between categories as appropriate. Prefer fuller, coherent rows and relevant adjacent skills over aggressive trimming; see the skills preferences below. Do not add unsupported skills, duplicate tokens, or empty categories.
- Preserve the preamble, macros, name, contact details, font, margins, sizes, spacing, heading styles, and all other template material. Do not add a summary, keywords section, commentary, hidden text, or new prose to the resume.

## Select and generate

1. Rank bullets by relevance and strength using the editable preferences. Cover central requirements with evidence, then add differentiating impact, technical depth, ownership, and collaboration. Avoid redundant examples. A strong substantive bullet can beat a shallow keyword match. Do not mechanically allocate equal bullet counts.
2. If a focused question or suggestion could materially improve the result, ask it while proceeding with independent work. Ask about priorities or factual ambiguity rather than asking for routine approval. If the answer would add or change a fact or rewrite a bullet, explain that a separate master update is needed; do not slip it into the tailored copy. An unfinished source bullet can be excluded and flagged, never silently repaired.
3. Use `scripts/resume.py catalog --master <path>` to obtain a fresh source hash, entry IDs, local bullet numbers, and available skill/stack tokens. Build a temporary JSON selection using the schema in [references/selection.md](references/selection.md). IDs are specific to this snapshot; never reuse a stale selection.
4. Use `scripts/resume.py render --master <path> --selection <json>` to create a draft in a temporary directory. Optimize the page using the fill loop below before passing `--publish`. The helper copies source slices and permits only the supported edits. Keep selection/build artifacts outside `resumes/`; publish only the `.tex` and validated `.pdf` in their versioned delivery folder. Inspect the source diff to confirm that every change is allowed. If the master structure changes beyond helper support, update the helper or make and audit the constrained edits directly; never substitute a new template.

## Use the full page

A one-page PDF is an initial constraint, not the stopping condition. Aim to use the template's full text area down to its existing bottom margin, with a small natural remainder. Preserve the master font, spacing, margins, and verbatim bullets; fill space with evidence rather than stretching the layout.

The layout checker reports `unused_height_pt`, `body_used_percent`, and `fill_target_met`. It compares the last visible text with the live template's text-area bottom, excluding the intentional page margin. The editable target is `max_unused_height_pt` in [references/layout.json](references/layout.json), initially 24 PDF points (one third of an inch). This allows a normal line or two of breathing room.

After each successful single-page compilation:

1. Review `skill_row_measurements` and the preview for sparse skills rows independently of the vertical fill target. Apply [preferences.md](references/preferences.md): retain relevant and role-adjacent master skills, combine compatible short categories, and reorder or split rows until each fits without wrapping. Recompile after changes; do not shrink typography or remove stronger accomplishments to pad skills.
2. If `fill_target_met` is false, review the strongest unused relevant bullets/projects. Add the best nonredundant evidence under its original entry and recompile. Favor useful accomplishments over extra skills rows; use relevant adjacent skills to improve horizontal coverage within those rows.
3. Keep an accepted selection as a checkpoint. If an addition spills to a second page or overflows, revert that addition and try a shorter relevant bullet, a different combination, or a better allocation across entries/projects. Do not stop after the first addition fails to fit; compare remaining plausible choices. Do not use irrelevant filler, duplicate evidence, rewrite bullets, or alter typography to consume space.
4. Stop when the measured target is met and no stronger composition is apparent, or when no remaining worthwhile combination fits. Even within the target, include a clearly valuable remaining bullet if it still fits comfortably. Inspect the final preview to confirm a balanced page, including the skills rows.

Publishing requires both safe layout and the fill target. Only if worthwhile remaining choices have been considered and cannot fit, use `--underfill-reason "<specific reason>"` to publish the best one-page composition and explain the unavoidable gap in the response. This exception never bypasses page count or overflow checks and must not be used merely to skip the fill loop.

## Validate one-page output

Use `python <skill>/scripts/check_layout.py --tex <draft.tex> --master <MasterResume.tex>`. This helper finds `pdflatex` on PATH or in standard per-user/system MiKTeX locations, including `%LOCALAPPDATA%/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe`. MiKTeX is installed on this machine. Pass `--compiler <executable>` only for a nonstandard location; restarting the application to refresh PATH is unnecessary when the fallback finds it.

The helper compiles a byte-identical temporary copy with shell escape disabled, nonstop/halt-on-error flags, and build artifacts in a temporary directory. It runs from the master directory so relative resources resolve. With MiKTeX, it enables automatic installation of missing TeX packages to avoid interactive prompts. It checks exactly one PDF page, overfull boxes, every project heading's measured width, and each skills row against its available line width; it exits nonzero if any check fails. `skill_row_measurements` reports width and utilization for each row to guide horizontal whitespace review; there is no fixed minimum row utilization. `resume.py render --publish` repeats these checks and refuses to publish an invalid candidate. Review the temporary PDF visually when rendering tools are available for clipping, overlap, and broken glyphs. Publication copies the validated, uninstrumented PDF alongside its LaTeX source automatically.

MiKTeX also supplies `pdftoppm.exe`, `pdfinfo.exe`, and `pdftotext.exe` beside `pdflatex.exe`, even if they are absent from PATH. Use `pdftoppm -png -singlefile -scale-to 1600 <temporary.pdf> <temporary-image-prefix>` to render a preview for image inspection, and `pdftotext` to check readable text extraction. Keep these artifacts in the temporary build directory.

For project-heading width checks, the helper instruments only a second disposable compilation copy: inside `\resumeProjectHeading`, it measures `\hbox{\small#1\hspace{2\tabcolsep}#2}` against `0.97\textwidth`, the width of the existing table. An overwide heading fails even if its unbreakable table produces no extra page. Measurement instrumentation never enters the delivered source. If the master changes this macro, adapt the probe to its actual width.

If it runs long or a heading overflows, remove the weakest/redundant whole bullets, remove a less relevant project, or trim allowed stack tokens and recompile. For overlong skills rows, first shorten a category label or regroup/split the tokens; trim less relevant skills only when useful regrouping cannot resolve the fit. Never fix fit by rewriting bullets or shrinking the template. If only template changes or factual edits would resolve a remaining problem, ask a focused question with the concrete conflict.

If compiler discovery or compilation fails, diagnose the concrete error. Keep the temporary `.tex` draft and explicitly report that layout is unverified; do not bypass the publication gate or claim success from source length alone. Do not install another system TeX distribution as an unannounced prerequisite.

## Naming and delivery

Save under the master directory's `resumes/`. Sanitize company and role individually to filesystem-safe names and join with `_`. First version is a `Company_Role/` folder containing `Company_Role.tex` and `Company_Role.pdf`; subsequent invocations use `Company_Role_2/`, `_3/`, etc., with matching filenames inside. Take the next highest existing iteration, counting both delivery folders and legacy loose `.tex`/`.pdf` files; preserve all prior files. Treat case-only differences as collisions on Windows. Iterate on the temporary draft rather than creating a new published version for every layout attempt. The helper reserves a new folder exclusively and copies the exact PDF that passed validation; auxiliary files stay temporary.

Return links to both the `.tex` and `.pdf`, the page/row validation status and remaining unused height, and brief notes about the strongest selections, title changes, and significant gaps or source issues. Keep every decision note and follow-up question outside the resume. Do not commit, push, or submit the resume unless asked.
