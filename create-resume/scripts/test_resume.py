"""Check flexible skills grouping without weakening source preservation."""

import copy
from pathlib import Path
import unittest

import resume


class SkillsRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.text = resume.source(Path(__file__).resolve().parents[2] / "MasterResume.tex")
        cls.catalog = resume.catalog(cls.raw, cls.text)
        cls.tokens = list(dict.fromkeys(token for tokens in cls.catalog["skills"].values()
                                       for token in tokens))
        cls.selection = {
            "master_sha256": cls.catalog["master_sha256"],
            "company": "Example", "role": "Intern",
            "entries": {entry["id"]: {"bullets": [1]} for entry in cls.catalog["entries"]},
            "skills": cls.catalog["skills"],
        }

    def render_skills(self, skills):
        selection = copy.deepcopy(self.selection)
        selection["skills"] = skills
        return resume.render(self.raw, self.text, selection)

    def test_custom_label_and_tokens_from_different_source_categories(self):
        tokens = [items[0] for items in self.catalog["skills"].values()]
        output = self.render_skills({"Backend & Tools": tokens})
        self.assertIn(r"\textbf{Backend \& Tools}{: " + ", ".join(tokens) + "}", output)
        # Regrouping must leave all other resume content and template material intact.
        baseline = self.render_skills(self.catalog["skills"])
        _, before = resume.parse(baseline)
        _, after = resume.parse(output)
        self.assertEqual(baseline[:before[0]], output[:after[0]])
        def without_rows(text, technical):
            start = technical[0]
            return resume.splice(text, [(start + line["start"], start + line["end"], "")
                                        for line in technical[2]])
        self.assertEqual(without_rows(baseline, before), without_rows(output, after))

    def test_can_split_into_more_rows_than_master(self):
        count = len(self.catalog["skills"]) + 1
        skills = {f"Group {i + 1}": [token] for i, token in enumerate(self.tokens[:count])}
        _, technical = resume.parse(self.render_skills(skills))
        self.assertEqual(len(technical[2]), count)
        self.assertEqual([line["tokens"][0] for line in technical[2]], self.tokens[:count])

    def test_legacy_selection_preserves_original_skill_lines(self):
        output = self.render_skills(self.catalog["skills"])
        _, original = resume.parse(self.text)
        _, rendered = resume.parse(output)
        self.assertEqual(self.text[original[0]:original[1]], output[rendered[0]:rendered[1]])

    def test_rejects_unsupported_duplicate_empty_and_multiline_values(self):
        token = self.tokens[0]
        invalid = [
            {"Tools": ["Invented skill"]},
            {"Tools": [token, token]},
            {"Backend": [token], "Tools": [token]},
            {"Tools": []},
            {"Tools\nInjected": [token]},
            {"": [token]},
        ]
        for skills in invalid:
            with self.subTest(skills=skills), self.assertRaises(ValueError):
                self.render_skills(skills)


if __name__ == "__main__":
    unittest.main()
