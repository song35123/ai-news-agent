import unittest

from ai_news_agent.dedupe import normalize_url, url_hash


class DedupeTests(unittest.TestCase):
    def test_normalize_url_trims_spaces(self):
        self.assertEqual(normalize_url(" https://example.com/a "), "https://example.com/a")

    def test_url_hash_is_stable_after_trimming(self):
        self.assertEqual(url_hash("https://example.com/a"), url_hash(" https://example.com/a "))

    def test_different_urls_have_different_hashes(self):
        self.assertNotEqual(url_hash("https://example.com/a"), url_hash("https://example.com/b"))


if __name__ == "__main__":
    unittest.main()

