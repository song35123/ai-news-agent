COMPANY_LOGOS = {
    "OpenAI": "openai.com",
    "Anthropic": "anthropic.com",
    "Google DeepMind": "deepmind.google",
    "Microsoft": "microsoft.com",
    "Meta": "meta.com",
    "Amazon": "amazon.com",
    "Nvidia": "nvidia.com",
    "Apple": "apple.com",
    "xAI": "x.ai",
    "Perplexity": "perplexity.ai",
    "Databricks": "databricks.com",
    "Scale AI": "scale.com",
    "DeepSeek": "deepseek.com",
    "Alibaba": "alibaba.com",
    "Tencent": "tencent.com",
    "Baidu": "baidu.com",
    "ByteDance": "bytedance.com",
    "Huawei": "huawei.com",
    "Moonshot AI": "moonshot.cn",
    "Zhipu AI": "zhipuai.cn",
    "MiniMax": "minimax.io",
    "01.AI": "01.ai",
    "Baichuan": "baichuan-ai.com",
    "SenseTime": "sensetime.com",
    "iFlytek": "iflytek.com",
    "Cambricon": "cambricon.com",
}


def company_badges(companies: str | None) -> list[dict]:
    """Build display metadata for company logo chips in the local UI."""
    badges = []
    for raw_name in (companies or "").split(","):
        name = raw_name.strip()
        if not name:
            continue
        domain = COMPANY_LOGOS.get(name)
        badges.append(
            {
                "name": name,
                "initial": logo_initial(name),
                "logo_url": favicon_url(domain) if domain else "",
            }
        )
    return badges


def favicon_url(domain: str) -> str:
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


def logo_initial(name: str) -> str:
    cleaned = name.replace(".", "").replace("-", " ").strip()
    if not cleaned:
        return "AI"
    parts = [part for part in cleaned.split() if part]
    if len(parts) >= 2:
        return "".join(part[0] for part in parts[:2]).upper()
    return cleaned[:2].upper()

