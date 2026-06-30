import time
import unittest

from ai_news_agent.parser import clean_text, parse_entry, parse_time


class ParserTests(unittest.TestCase):
    def test_clean_text_strips_html_and_whitespace(self):
        self.assertEqual(clean_text("<p>Hello&nbsp;<b>AI</b></p>"), "Hello AI")

    def test_parse_entry_requires_title_and_url(self):
        self.assertIsNone(parse_entry({"title": "No URL"}, "Source"))
        self.assertIsNone(parse_entry({"link": "https://example.com"}, "Source"))

    def test_parse_entry_builds_news_item(self):
        item = parse_entry(
            {
                "title": "<b>OpenAI news</b>",
                "link": "https://example.com/openai",
                "summary": "<p>New model</p>",
            },
            "Example",
        )

        self.assertEqual(item.title, "OpenAI news")
        self.assertEqual(item.summary, "New model")
        self.assertEqual(item.source, "Example")

    def test_parse_time_from_struct_time_uses_utc(self):
        parsed = time.gmtime(0)
        self.assertEqual(parse_time({"published_parsed": parsed}), "1970-01-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

