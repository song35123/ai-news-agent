from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_DIR = Path("output/pdf")
APP_ICON_PATH = Path("src/ai_news_agent/static/app_icon.png")
PDF_FONT_NAME = "AppChinese"


class Rule(Flowable):
    def __init__(self, color=colors.HexColor("#dce4e8"), width=0.8):
        super().__init__()
        self.color = color
        self.width = width

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.width)
        self.canv.line(0, 0, self._frame._width, 0)


def default_pdf_path() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"ai_news_brief_{datetime.now().date().isoformat()}.pdf"


def build_pdf_report(rows: list, stats: dict, translation_status: dict, output_path: Path) -> Path:
    """Create a compact Chinese PDF brief from the current homepage data."""
    register_chinese_font()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="中美 AI 公司新闻观察",
        author="AI News Agent",
    )
    story = []
    styles = make_styles()

    header_cells = []
    if APP_ICON_PATH.exists():
        header_cells.append(Image(str(APP_ICON_PATH), width=22 * mm, height=22 * mm))
    else:
        header_cells.append(Paragraph("AI", styles["LogoFallback"]))

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    header_cells.append(
        [
            Paragraph("中美 AI 公司新闻观察", styles["Title"]),
            Paragraph(f"前 10 条中文科技新闻简报 - 生成时间：{generated}", styles["Subtitle"]),
        ]
    )
    header = Table([header_cells], colWidths=[28 * mm, 131 * mm])
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 9 * mm))

    story.append(stats_table(stats, translation_status, styles))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("新闻简报", styles["SectionTitle"]))
    story.append(Spacer(1, 3 * mm))

    if not rows:
        story.append(Paragraph("当前没有通过审查的新闻。请先刷新新闻。", styles["Body"]))
    else:
        for index, row in enumerate(rows[:10], start=1):
            story.append(news_block(index, row, styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output_path


def make_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "TitleZh",
            parent=base["Title"],
            fontName=PDF_FONT_NAME,
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#17202a"),
            spaceAfter=2,
        ),
        "Subtitle": ParagraphStyle(
            "SubtitleZh",
            parent=base["Normal"],
            fontName=PDF_FONT_NAME,
            fontSize=9.8,
            leading=14,
            textColor=colors.HexColor("#667085"),
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitleZh",
            parent=base["Heading2"],
            fontName=PDF_FONT_NAME,
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#087f72"),
        ),
        "NewsTitle": ParagraphStyle(
            "NewsTitleZh",
            parent=base["Heading3"],
            fontName=PDF_FONT_NAME,
            fontSize=12.8,
            leading=17,
            textColor=colors.HexColor("#17202a"),
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "BodyZh",
            parent=base["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=9.8,
            leading=15,
            textColor=colors.HexColor("#35424c"),
        ),
        "Meta": ParagraphStyle(
            "MetaZh",
            parent=base["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=8.8,
            leading=12,
            textColor=colors.HexColor("#667085"),
        ),
        "Chip": ParagraphStyle(
            "ChipZh",
            parent=base["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=8.6,
            leading=11,
            textColor=colors.HexColor("#145c52"),
            alignment=TA_CENTER,
        ),
        "LogoFallback": ParagraphStyle(
            "LogoFallback",
            parent=base["Title"],
            fontName=PDF_FONT_NAME,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
    }


def stats_table(stats: dict, translation_status: dict, styles: dict) -> Table:
    data = [
        [
            stat_cell("已保存", stats.get("total", 0), styles),
            stat_cell("通过审查", stats.get("relevant", 0), styles),
            stat_cell("已翻译", stats.get("translated", 0), styles),
        ],
        [
            Paragraph(f"翻译状态：{translation_status.get('label', '')}", styles["Meta"]),
            Paragraph("默认范围：中美 AI 科技公司相关新闻", styles["Meta"]),
            Paragraph("来源：公开 RSS", styles["Meta"]),
        ],
    ]
    table = Table(data, colWidths=[53 * mm, 53 * mm, 53 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef7f5")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#dce4e8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce4e8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def stat_cell(label: str, value: int, styles: dict) -> list:
    return [
        Paragraph(f"<font color='#087f72' size='18'>{value}</font>", styles["Body"]),
        Paragraph(label, styles["Meta"]),
    ]


def news_block(index: int, row: dict, styles: dict) -> KeepTogether:
    title = row["title_zh"] or row["title"]
    summary = row["summary_zh"] or row["summary"] or "暂无摘要。"
    published = row["published_at"] or row["fetched_at"]
    companies = row["companies"] or "未标注公司"
    regions = row["regions"] or "未标注地区"
    reason = row["review_reason"] or "通过本地规则审查"
    content_type = row.get("content_type") or "未分类"

    content = [
        Rule(colors.HexColor("#dce4e8")),
        Spacer(1, 4 * mm),
        Paragraph(f"{index}. {escape(title)}", styles["NewsTitle"]),
        Paragraph(
            f"{escape(row['source'])} · {escape(published)} · {escape(content_type)} · 相关度 {row['relevance_score']}",
            styles["Meta"],
        ),
        Spacer(1, 2 * mm),
        chip_table(companies, regions, styles),
        Spacer(1, 2 * mm),
        Paragraph(escape(summary), styles["Body"]),
        Spacer(1, 2 * mm),
        Paragraph(f"审查理由：{escape(reason)}", styles["Meta"]),
        Paragraph(f"链接：{escape(row['url'])}", styles["Meta"]),
        Spacer(1, 5 * mm),
    ]
    return KeepTogether(content)


def chip_table(companies: str, regions: str, styles: dict) -> Table:
    chips = [companies, regions]
    data = [[Paragraph(escape(chip), styles["Chip"]) for chip in chips]]
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fbf8")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8ddd5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8ddd5")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(PDF_FONT_NAME, 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(18 * mm, 9 * mm, "AI News Agent - 本地生成")
    canvas.drawRightString(192 * mm, 9 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def escape(text: object) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def register_chinese_font() -> None:
    candidates = [
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            registerFont(TTFont(PDF_FONT_NAME, str(path)))
            return
    raise RuntimeError("没有找到可用于 PDF 的中文字体。")
