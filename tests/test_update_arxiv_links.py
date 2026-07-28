import unittest

import update_arxiv_links


class MetadataMatchingTests(unittest.TestCase):
    def test_requires_matching_title_and_author(self):
        arxiv_title = "Off-diagonal Ramsey numbers"
        arxiv_authors = ["Domagoj Bradač"]
        unrelated_paper = {
            "title": "Off-diagonal book Ramsey numbers",
            "authors": ["Conlon", "Fox", "Wigderson"],
        }

        self.assertGreaterEqual(
            update_arxiv_links.title_similarity(
                arxiv_title,
                unrelated_paper["title"],
            ),
            update_arxiv_links.TITLE_THRESHOLD,
        )
        self.assertFalse(
            update_arxiv_links.metadata_matches(
                arxiv_title,
                arxiv_authors,
                unrelated_paper,
            )
        )

        matching_paper = {"title": arxiv_title, "authors": ["Bradac"]}
        self.assertTrue(
            update_arxiv_links.metadata_matches(
                arxiv_title,
                arxiv_authors,
                matching_paper,
            )
        )
