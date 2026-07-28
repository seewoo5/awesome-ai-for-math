import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import update_arxiv_links


class CrossRefMatchingTests(unittest.TestCase):
    @patch("update_arxiv_links.requests.get")
    def test_rejects_similar_title_with_different_authors(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1017/s0963548322000360",
                        "title": ["Off-diagonal book Ramsey numbers"],
                        "author": [
                            {"family": "Conlon"},
                            {"family": "Fox"},
                            {"family": "Wigderson"},
                        ],
                        "container-title": [
                            "Combinatorics, Probability and Computing"
                        ],
                        "published": {"date-parts": [[2023]]},
                    }
                ]
            }
        }
        mock_get.return_value = response

        result = update_arxiv_links.query_crossref_by_title(
            "Off-diagonal Ramsey numbers",
            ["Domagoj Bradač"],
        )

        self.assertIsNone(result)

    @patch("update_arxiv_links.requests.get")
    def test_accepts_similar_title_with_matching_author(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/example",
                        "title": ["Off-diagonal Ramsey numbers"],
                        "author": [{"family": "Bradac"}],
                        "container-title": ["Example Journal"],
                        "published": {"date-parts": [[2026]]},
                    }
                ]
            }
        }
        mock_get.return_value = response

        result = update_arxiv_links.query_crossref_by_title(
            "Off-diagonal Ramsey numbers",
            ["Domagoj Bradač"],
        )

        self.assertEqual(result["doi"], "10.1234/example")
        self.assertEqual(result["venue"], "Example Journal 2026")


class ReadmeUpdateTests(unittest.TestCase):
    @patch("update_arxiv_links.time.sleep")
    @patch("update_arxiv_links.query_crossref_by_title", return_value=None)
    @patch("update_arxiv_links.query_crossref_by_doi")
    @patch("update_arxiv_links.query_arxiv")
    def test_rejects_mismatched_doi_supplied_by_arxiv(
        self,
        mock_arxiv,
        mock_crossref_by_doi,
        _mock_crossref_by_title,
        _mock_sleep,
    ):
        mock_arxiv.return_value = {
            "title": "Off-diagonal Ramsey numbers",
            "doi": "10.1017/s0963548322000360",
            "authors": ["Domagoj Bradač"],
        }
        mock_crossref_by_doi.return_value = {
            "doi": "10.1017/s0963548322000360",
            "title": "Off-diagonal book Ramsey numbers",
            "authors": ["Conlon", "Fox", "Wigderson"],
            "venue": "Combinatorics, Probability and Computing 2023",
        }
        row = (
            "| **[Off-diagonal Ramsey numbers]"
            "(https://arxiv.org/abs/2605.28793)** "
            "| Combinatorics, LLM | arXiv 2026 |  |\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            readme = Path(temp_dir) / "README.md"
            readme.write_text(row, encoding="utf-8")

            update_arxiv_links.update_readme(str(readme), str(readme))

            self.assertEqual(readme.read_text(encoding="utf-8"), row)


if __name__ == "__main__":
    unittest.main()
