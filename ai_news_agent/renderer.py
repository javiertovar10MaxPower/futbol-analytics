from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .researcher import NewsItem
from .sources import CATEGORIES


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(items: list[NewsItem], since: date, today: date) -> str:
    by_category: dict[str, list[NewsItem]] = {key: [] for key in CATEGORIES}
    for item in items:
        if item.category in by_category:
            by_category[item.category].append(item)

    sections = [
        (cat_id, CATEGORIES[cat_id], cat_items)
        for cat_id, cat_items in by_category.items()
        if cat_items
    ]

    highlights = [i for i in items if i.importance >= 4][:3]

    template = _env.get_template("email.html.j2")
    return template.render(
        today=today.isoformat(),
        since_date=since.isoformat(),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        total_items=len(items),
        categories=list(CATEGORIES.keys()),
        sections=sections,
        highlights=highlights,
    )
