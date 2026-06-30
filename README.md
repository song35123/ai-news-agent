# AI News Agent

本地运行的中美 AI 公司新闻观察工具。它从公开 RSS 抓取新闻，自动审查是否属于目标范围，保存到本地数据库，并用本地网页展示。

当前目标新闻范围：

- 美国 AI 科技公司，例如 OpenAI、Anthropic、Google DeepMind、Microsoft、Meta、Nvidia、xAI、Perplexity
- 中国 AI 科技公司，例如 DeepSeek、阿里通义、腾讯混元、百度文心、字节豆包、华为、月之暗面、智谱、MiniMax
- 与这些公司、模型、芯片、智能体、算力、训练、推理等 AI 主题直接相关的新闻

第一版仍然遵守这些边界：

- 不登录网站
- 不绕过反爬、验证码或付费墙
- 不抓取付费内容
- 默认只抓取公开 RSS

## 最简单的用法

Windows 下双击：

```text
start_news_app.bat
```

或者直接双击桌面快捷方式：

```text
AI News Agent
```

它会启动本地网页：

```text
http://127.0.0.1:5000
```

页面里主要用这几个按钮：

- `一键更新今日简报`：主流程，抓取今日新闻、审查、翻译最新内容，并生成 Markdown/PDF
- `刷新新闻`：抓取公开 RSS，并自动审查是否属于中美 AI 公司新闻
- `修复/安装离线翻译`：安装或修复本地翻译模型
- `刷新并翻译`：抓取新闻后翻译最新通过审查的内容
- `生成简报`：生成 Markdown 简报
- `下载 PDF`：下载“主页面概览 + 前 10 条中文科技新闻”的 PDF 简报
- `运行诊断`：检查依赖、数据库和翻译状态

## 桌面快捷方式

项目提供了一个本地应用图标和快捷方式生成脚本：

```powershell
python create_desktop_shortcut.py
```

它会生成：

- 应用图标：`assets/ai_news_agent.ico`
- 网页图标：`src/ai_news_agent/static/app_icon.png`
- 桌面快捷方式：`AI News Agent.lnk`

快捷方式使用静默启动脚本 `start_news_app_silent.vbs`，双击后会直接打开浏览器，不会弹出命令行窗口。如果启动失败，可以运行 `start_news_app.bat` 查看错误信息。

## 中文翻译

默认推荐使用离线翻译模型，不使用 OpenAI API，不按条收费。

第一次使用翻译时，在网页里点击：

```text
修复/安装离线翻译
```

它会安装 Argos Translate，并下载英文到中文的离线模型。这个过程只需要做一次。

如果翻译失败，并提示模型文件缺失，也点击这个按钮重新修复即可。程序会清理损坏的旧模型目录，再重新安装。

如果离线模型在当前环境里仍不可用，程序会自动退回到 `deep-translator` 的免费网页翻译。这个方案不需要 OpenAI API，但依赖网络，可能受到频率限制。

翻译结果会缓存到 `data/news.db`，下次打开页面不会重复翻译同一条新闻。

如果你自己部署了 LibreTranslate，也可以用环境变量接入：

```powershell
$env:LIBRETRANSLATE_URL="http://127.0.0.1:5001"
python start_news_app.py
```

## 审查逻辑

项目使用透明的本地规则做第一版新闻审查：

1. 标题、摘要或来源中是否命中中美 AI 公司名称或产品名
2. 是否命中 AI 相关关键词，例如 LLM、agent、GPU、training、inference、大模型、智能体、算力
3. 生成相关度分数、公司标签、地区标签和审查理由

默认页面只展示通过审查的新闻。你也可以在页面里把范围切换为 `全部抓取内容`，查看被过滤掉的内容。

## 结果在哪里

- 本地网页：`http://127.0.0.1:5000`
- 数据库：`data/news.db`
- Markdown 简报：`briefs/YYYY-MM-DD.md`
- PDF 简报：`output/pdf/ai_news_brief_YYYY-MM-DD.pdf`
- 新闻源配置：`config/sources.yaml`
- 运行日志：`logs/app.log`
- 启动错误：`logs/startup_error.log`

## 一条命令生成简报

如果你不想打开网页，只想生成当天简报：

```powershell
python get_news.py
```

不自动打开简报：

```powershell
python get_news.py --no-open
```

生成最近 3 天、最多 50 条：

```powershell
python get_news.py --days 3 --limit 50
```

## 运行测试

项目使用 Python 标准库 `unittest`，不需要额外测试框架：

```powershell
python -m unittest discover -s tests
```

## 修改新闻源

新闻源配置在：

```text
config/sources.yaml
```

格式示例：

```yaml
sources:
  - name: TechCrunch AI
    url: https://techcrunch.com/category/artificial-intelligence/feed/
    enabled: true
```

把 `enabled` 改成 `false` 可以临时关闭某个新闻源。

## 项目结构

```text
ai-news-agent/
  start_news_app.bat
  start_news_app.py
  get_news.py
  requirements.txt
  config/
    sources.yaml
  data/
    news.db
  briefs/
    YYYY-MM-DD.md
  src/
    ai_news_agent/
      web.py
      reviewer.py
      translator.py
      storage.py
      fetcher.py
      parser.py
      brief.py
```
