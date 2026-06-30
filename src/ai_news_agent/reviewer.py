from dataclasses import dataclass

from .models import utc_now_iso


REVIEW_RULE_VERSION = "2026-06-30-v3"


@dataclass(frozen=True)
class Company:
    name: str
    region: str
    aliases: tuple[str, ...]
    product_aliases: tuple[str, ...] = ()


COMPANIES = [
    Company("OpenAI", "美国", ("openai",), ("chatgpt", "codex", "sora", "gpt-4", "gpt-5")),
    Company("Anthropic", "美国", ("anthropic",), ("claude", "claude code")),
    Company("Google DeepMind", "美国", ("deepmind", "google deepmind"), ("gemini", "alphafold")),
    Company("Microsoft", "美国", ("microsoft",), ("copilot", "azure ai")),
    Company("Meta", "美国", ("meta",), ("llama",)),
    Company("Amazon", "美国", ("amazon",), ("aws bedrock", "bedrock")),
    Company("Nvidia", "美国", ("nvidia",), ("blackwell", "h100", "h200", "b200")),
    Company("Apple", "美国", ("apple",), ("apple intelligence", "apple ai")),
    Company("xAI", "美国", ("xai", "x.ai"), ("grok",)),
    Company("Perplexity", "美国", ("perplexity",), ()),
    Company("Databricks", "美国", ("databricks",), ("mosaicml",)),
    Company("Scale AI", "美国", ("scale ai",), ()),
    Company("Cursor", "美国", ("cursor",), ()),
    Company("DeepSeek", "中国", ("deepseek", "深度求索"), ("deepseek-r1", "deepseek-v3")),
    Company("Alibaba", "中国", ("alibaba", "aliyun", "阿里"), ("qwen", "tongyi", "通义")),
    Company("Tencent", "中国", ("tencent", "腾讯"), ("hunyuan", "混元")),
    Company("Baidu", "中国", ("baidu", "百度"), ("ernie", "文心")),
    Company("ByteDance", "中国", ("bytedance", "字节"), ("doubao", "豆包")),
    Company("Huawei", "中国", ("huawei", "华为"), ("昇腾", "盘古", "ascend")),
    Company("Moonshot AI", "中国", ("moonshot", "月之暗面"), ("kimi",)),
    Company("Zhipu AI", "中国", ("zhipu", "智谱"), ("glm",)),
    Company("MiniMax", "中国", ("minimax",), ("abab",)),
    Company("01.AI", "中国", ("01.ai", "零一万物"), ("yi model",)),
    Company("Baichuan", "中国", ("baichuan", "百川智能"), ()),
    Company("SenseTime", "中国", ("sensetime", "商汤"), ()),
    Company("iFlytek", "中国", ("iflytek", "讯飞"), ("sparkdesk",)),
    Company("Cambricon", "中国", ("cambricon", "寒武纪"), ()),
]

AI_TERMS = (
    "artificial intelligence",
    "generative ai",
    "llm",
    "large language model",
    "foundation model",
    "reasoning model",
    "ai agent",
    "chatbot",
    "inference",
    "training",
    "ai chip",
    "gpu",
    "accelerator",
    "大模型",
    "人工智能",
    "智能体",
    "算力",
)

WEAK_AI_TERMS = ("ai", "model", "agent", "chip", "cuda")

NEWS_ACTION_TERMS = (
    "announce",
    "announces",
    "announced",
    "launch",
    "launches",
    "released",
    "release",
    "unveil",
    "unveils",
    "deal",
    "partnership",
    "pricing",
    "investment",
    "funding",
    "acquisition",
    "lawsuit",
    "policy",
    "government",
    "security",
    "malware",
    "vulnerability",
    "data center",
    "chip investment",
    "计划",
    "发布",
    "推出",
    "合作",
    "投资",
    "融资",
    "收购",
    "定价",
    "安全",
)

TECHNICAL_ARTICLE_TERMS = (
    "tutorial",
    "guide",
    "github",
    "repo",
    "repository",
    "open source",
    "paper",
    "arxiv",
    "benchmark",
    "protocol",
    "local development",
    "library",
    "framework",
    "course",
    "how to",
)

EXCLUDE_TERMS = (
    "show hn",
    "ask hn",
    "comments",
    "resume",
    "ats",
    "max planck",
    "journal retract",
    "pollen",
    "age verification",
)

STRONG_KEEP_TERMS = (
    "claude code",
    "openai",
    "deepseek",
    "qwen",
    "gemini",
    "llama",
    "chatgpt",
    "codex",
    "blackwell",
    "h100",
    "h200",
    "b200",
    "nvidia ai",
)

AI_FOCUSED_SOURCES = (
    "mit technology review ai",
    "techcrunch ai",
    "venturebeat ai",
    "the decoder",
    "openai",
)

LOW_TRUST_SOURCES = ("hacker news",)


def review_news(title: str, summary: str, source: str = "") -> dict:
    """Classify whether an item is target AI-company news."""
    text = f"{title}\n{summary}".lower()
    source_text = source.lower()
    full_text = f"{text}\n{source_text}"

    matched_companies = []
    matched_regions = []
    matched_products = []

    for company in COMPANIES:
        company_hit = any(alias.lower() in text for alias in company.aliases)
        product_hits = [alias for alias in company.product_aliases if alias.lower() in text]
        if company_hit or product_hits:
            matched_companies.append(company.name)
            matched_regions.append(company.region)
            matched_products.extend(product_hits)

    matched_terms = [term for term in AI_TERMS if term.lower() in full_text]
    weak_terms = [term for term in WEAK_AI_TERMS if term.lower() in text]
    news_terms = [term for term in NEWS_ACTION_TERMS if term.lower() in text]
    technical_terms = [term for term in TECHNICAL_ARTICLE_TERMS if term.lower() in text]
    exclude_terms = [term for term in EXCLUDE_TERMS if term.lower() in text]
    strong_keep_terms = [term for term in STRONG_KEEP_TERMS if term.lower() in text]

    source_is_ai_focused = source_text in AI_FOCUSED_SOURCES
    source_is_low_trust = source_text in LOW_TRUST_SOURCES
    content_type = classify_content(
        source_is_low_trust=source_is_low_trust,
        news_terms=news_terms,
        technical_terms=technical_terms,
        exclude_terms=exclude_terms,
    )

    score = 0
    reasons = []

    if matched_companies:
        score += 45
        reasons.append("命中中美 AI 科技公司或产品")
    if matched_products:
        score += 30
        reasons.append("命中强相关 AI 产品或模型")
    if matched_terms:
        score += min(20, 5 * len(matched_terms))
        reasons.append("命中 AI 技术语境")
    if news_terms:
        score += 20
        reasons.append("命中公司新闻动作")
    if source_is_ai_focused:
        score += 10
        reasons.append("来源属于 AI 专题源")
    if len(set(matched_regions)) >= 2:
        score += 5
        reasons.append("同时涉及中美公司")
    if weak_terms and not (matched_products or matched_terms):
        reasons.append("仅命中弱 AI 词，不能单独通过")
    if source_is_low_trust:
        score -= 15
        reasons.append("Hacker News 默认降权")
    if technical_terms:
        score -= 10 if source_is_ai_focused else 20
        reasons.append("偏技术文章")
    if exclude_terms:
        score -= 60
        reasons.append("命中排除规则")

    score = max(0, min(score, 100))
    has_company_scope = bool(matched_companies)
    has_ai_context = bool(matched_products or matched_terms or source_is_ai_focused)
    has_news_context = bool(news_terms or source_is_ai_focused or strong_keep_terms)
    low_trust_technical_noise = source_is_low_trust and technical_terms and not news_terms
    excluded = bool(exclude_terms) or low_trust_technical_noise

    is_relevant = (
        has_company_scope
        and has_ai_context
        and has_news_context
        and not excluded
        and score >= 70
    )

    if not reasons:
        reasons.append("未命中目标公司或 AI 新闻语境")

    return {
        "is_relevant": 1 if is_relevant else 0,
        "relevance_score": score,
        "companies": ", ".join(dict.fromkeys(matched_companies)),
        "regions": ", ".join(dict.fromkeys(matched_regions)),
        "content_type": content_type,
        "review_reason": "；".join(reasons),
        "reviewed_at": utc_now_iso(),
        "review_version": REVIEW_RULE_VERSION,
    }


def classify_content(
    *,
    source_is_low_trust: bool,
    news_terms: list[str],
    technical_terms: list[str],
    exclude_terms: list[str],
) -> str:
    if exclude_terms:
        return "excluded"
    if source_is_low_trust and not news_terms:
        return "community_discussion"
    if technical_terms and not news_terms:
        return "technical_article"
    return "company_news"
