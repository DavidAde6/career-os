# Editable resume preferences

Edit this file to evolve selection biases without changing the renderer. Explicit invocation preferences take priority. Factual fidelity and preservation rules remain in SKILL.md.

## Selection priorities

- First cover what the target role actually does and its central requirements.
- Include internship availability only when the job description explicitly asks candidates to state their availability or start/end dates on the resume. Otherwise omit the availability bullet, even when it exists in the master.
- Within relevant evidence, prefer substantial impact, technical specificity, engineering judgment, scope, ownership, and unusually strong achievements over vague responsibilities or superficial keyword matches.
- Favor bullets that explain enough of the work to understand the engineering challenge and contribution. Useful specifics can outweigh a metric with little context.
- Give differentiating technical ability, rare experience, and demonstrated collaboration/communication appropriate weight. Use evidence such as architecture decisions, stakeholder translation, cross-team integration, or partner engineering work rather than generic soft-skill labels.
- Consider company/product values explicitly present in the description. Treat inferred hiring emphasis as a tie-breaker, not a reason to discard better evidence.
- Avoid repetition across roles/projects. Keep three experience entries when they earn their space; choose projects and bullet counts based on marginal relevance and the actual page budget.
- Prefer strong complete bullets. Flag unfinished claims, typos, ellipses, or ambiguous metrics if they materially weaken a choice; do not repair them in the copy.

## Page utilization

- Use the full available page length within the master's existing margins. A sparse one-page draft is unfinished while worthwhile master content can still fit.
- Fill remaining space with the strongest unused relevant accomplishments, technical depth, or a worthwhile project. Avoid padding the skills list or adding weak/redundant bullets just to hit a measurement.
- Recompile after additions and compare shorter alternatives when a strong addition causes a second page. Keep the best valid composition.
- Adjust the bottom-gap target in [layout.json](layout.json); the default is 24 PDF points within the text area, excluding the original bottom margin. This is a content-selection target, not permission to change the template.

## Titles

- Use exactly `Software Engineering Intern` for internship experience titles, including both Nokia roles and AFM.
- Do not append specializations or change experience titles to match the target role unless the user explicitly requests it.
- Preserve actual seniority and employment type; do not imply unsupported responsibilities.

## Project stacks and skills

- Keep project names unchanged and the full project heading on one rendered row. Prioritize the few technologies that best describe the selected work and match the target.
- Tailor category labels and groupings to the work: Backend, Full Stack, AI / ML, Cloud / Tools, or another concise, accurate label. Categories need not match the master labels; tokens may move between categories or be combined into a broader row.
- Prefer concise category labels without slashes, using simple names or an ampersand where useful. Preserve slashes within source technology names such as HTML/CSS and GitLab CI/CD.
- Lean toward retaining more relevant skills rather than shortening the list to literal posting keywords. Include credible role-adjacent master skills: for example, a Kubernetes/cloud role can warrant AWS, GCP, Azure, Docker, and related infrastructure tools even when the posting does not name each one. Adjacency justifies selection, never a new factual claim.
- Aim for coherent rows that use most of the available width without wrapping or overflowing. Broaden sparse rows with relevant adjacent skills; combine compatible short categories when that yields a cleaner fit. Reorder or split an overlong row before dropping useful skills. A shorter final row is fine when additional tokens would be weak filler; there is no mandatory row count or utilization percentage.
- Keep the section readable and balanced across the skills useful for the role. Use the checker's per-row widths and the rendered preview, not token counts or source-line length, to assess fit. Horizontal skills whitespace is a separate concern from the page's bottom gap; do not displace stronger accomplishments just to lengthen the skills inventory.
- Preserve master spelling of technology tokens, select each at most once, and use only tokens already in the master's technical skills catalog. Custom labels describe groupings, not new credentials or proficiency claims. Preserve the master row typography and spacing.

## Template ownership

`MasterResume.tex` is the live template. To change typography, contact details, source bullets, or other facts, request a separate edit of that file. Changing preferences here does not authorize changing the master during resume generation.
