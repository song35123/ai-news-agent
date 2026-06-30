import unittest

from ai_news_agent.reviewer import review_news


class ReviewerTests(unittest.TestCase):
    def test_rejects_pdf_false_positive_open_memory_protocol(self):
        result = review_news(
            "Open Memory Protocol - One Memory Store for Claude, ChatGPT, Cursor",
            "Comments",
            "Hacker News",
        )

        self.assertEqual(result["is_relevant"], 0)
        self.assertEqual(result["content_type"], "excluded")

    def test_rejects_generic_google_event_from_hacker_news(self):
        result = review_news(
            "Pollen tried to remove article, and Google helped",
            "Comments",
            "Hacker News",
        )

        self.assertEqual(result["is_relevant"], 0)

    def test_rejects_cuda_without_company_news_context(self):
        result = review_news(
            "CUDA tutorial for faster matrix multiplication",
            "A technical article about kernels and model experiments.",
            "Hacker News",
        )

        self.assertEqual(result["is_relevant"], 0)

    def test_keeps_claude_code_security_news(self):
        result = review_news(
            "Claude Code runs a GitHub repo's hidden malware without verification",
            "Attackers can gain control through unsafe agent execution.",
            "The Decoder",
        )

        self.assertEqual(result["is_relevant"], 1)
        self.assertIn("Anthropic", result["companies"])

    def test_keeps_qwen_model_article_from_ai_source(self):
        result = review_news(
            "Qwen 3.6 27B is the sweet spot for local development",
            "A model-focused article for local inference.",
            "The Decoder",
        )

        self.assertEqual(result["is_relevant"], 1)
        self.assertIn("Alibaba", result["companies"])
        self.assertEqual(result["content_type"], "technical_article")

    def test_keeps_nvidia_ai_chip_news(self):
        result = review_news(
            "Nvidia Blackwell demand surges as AI training clusters expand",
            "Cloud providers are buying more AI chips for inference and training.",
            "TechCrunch AI",
        )

        self.assertEqual(result["is_relevant"], 1)
        self.assertIn("Nvidia", result["companies"])


if __name__ == "__main__":
    unittest.main()

