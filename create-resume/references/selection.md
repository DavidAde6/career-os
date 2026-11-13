# Renderer selection format

Run the helper using its absolute path, or resolve it relative to the skill folder. It requires Python 3.10+ and no third-party packages. Paths below are examples; use the selected project's actual master.

```text
python <skill>/scripts/resume.py catalog --master <project>/MasterResume.tex
python <skill>/scripts/resume.py render --master <project>/MasterResume.tex --selection <temporary>/selection.json
python <skill>/scripts/check_layout.py --tex <draft.tex> --master <project>/MasterResume.tex
python <skill>/scripts/resume.py render --master <project>/MasterResume.tex --selection <temporary>/selection.json --publish
```

Without `--publish`, `render` writes a new temporary draft and prints its absolute path. With `--publish`, it verifies layout and page utilization using MiKTeX/pdfLaTeX, then reserves a versioned folder under the project's `resumes/` containing matching `.tex` and `.pdf` files. It copies the exact uninstrumented PDF that passed validation. The JSON result includes `path` (LaTeX), `pdf`, and `directory` for delivery, plus `validation` with temporary build paths. Versioning counts existing folders and legacy loose `.tex`/`.pdf` files case-insensitively and preserves them. Render only once for final publication; temporary drafts/builds do not consume version numbers. The standalone layout checker returns unused height, the fill-target status, and the temporary PDF location for visual inspection; it never publishes files. Auxiliary files stay temporary. An underfilled draft returns nonzero even when `layout_verified` is true: add relevant content and recompile until `publication_ready` is true. The target is editable in `layout.json`. Only after worthwhile remaining content has been exhausted, `--underfill-reason "specific reason"` permits an otherwise valid underfilled publication and records the explanation outside the resume.

The catalog gives the current `master_sha256`, entries in source order, one-based local bullet numbers, allowed project-stack tokens, and technical-skill categories/tokens. The helper is intentionally tailored to this master's `resumeSubheading`, `resumeProjectHeading`, `resumeItem`, and technical-skills macros. It fails on unsupported structures rather than replacing the template.

Example selection shape (replace the hash and choices with values from the current catalog):

```json
{
  "master_sha256": "hash from the current catalog",
  "company": "Example Company",
  "role": "Software Engineering Intern",
  "entries": {
    "experience-1": {
      "bullets": [1, 4, 7],
      "title": "Software Engineering Intern - AI Platform"
    },
    "experience-2": {"bullets": [2, 3]},
    "experience-3": {"bullets": [1]},
    "projects-1": {"bullets": [3, 6], "stack": ["LangGraph", "PostgreSQL", "FastAPI"]},
    "education-1": {"bullets": [1, 2]}
  },
  "skills": {
    "Backend & Languages": ["Python", "TypeScript", "SQL", "FastAPI", "Flask", "REST", "PostgreSQL", "Redis"],
    "AI / ML": ["LangGraph", "OpenAI Agents SDK", "Google ADK", "RAG", "TensorFlow", "Pandas", "NumPy"],
    "Cloud / Tools": ["AWS", "GCP", "Azure", "Docker", "Kubernetes", "Linux", "Git", "GitLab CI/CD", "GitHub Actions"]
  }
}
```

Only included experience/project entries survive. Education entries are required; their bullet lists can be selected, including an empty list, but their metadata cannot be edited. Retained experience/project entries need at least one bullet. Bullet list order controls bullet order; entry and section order remain as in the master. Omit a title or stack to keep its original value. The role field labels the target filename; a title override separately controls each experience heading.

`skills` maps output row labels to ordered token lists. Labels are nonempty, single-line plain text and may be renamed, merged, or split independently of the catalog's original categories; special characters such as `&` are escaped automatically. Choose tokens from the union of all catalog skill categories, using their exact spelling. Each token may appear only once across the section. Existing selections with original category labels remain supported. The row count can differ from the master, but the helper preserves its row format, surrounding template, and spacing. Use concise descriptive labels without adding proficiency or credential claims.

The example demonstrates custom grouping and role-adjacent coverage, not a mandatory inventory or row layout. After rendering, review `skill_row_measurements` and the PDF: combine sparse compatible rows, retain useful adjacent master tokens, and reorder or split overlong rows. Every skills row must fit its available line width without wrapping; the publication gate rejects an overwide row even when LaTeX wraps it without an overfull-box warning. No fixed minimum width utilization is enforced.

Project stack choices include original heading tokens plus exact master skill tokens explicitly mentioned in that project's own content. This prevents accidentally attributing a tool from another role/project. No free-form LaTeX is accepted for titles; special characters are escaped.

The helper preserves all master material outside selected entry/bullet slices, role-title arguments, project-stack arguments, and technical-skill lines. Inspect the final diff and compile to validate layout: deterministic source copying proves fidelity, not page fit. Future structural master edits may require adapting the helper.
