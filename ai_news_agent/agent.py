import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from . import emailer, renderer, researcher

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente semanal de noticias de IA → Outlook")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No envía email; escribe el HTML en out/preview.html",
    )
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--min-items", type=int, default=12)
    parser.add_argument("--max-items", type=int, default=18)
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    load_dotenv()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 2

    if not args.dry_run:
        missing = [k for k in ("OUTLOOK_EMAIL", "OUTLOOK_APP_PASSWORD", "RECIPIENT_EMAIL") if not os.environ.get(k)]
        if missing:
            print(f"ERROR: missing env vars for sending email: {missing}", file=sys.stderr)
            return 2

    logger.info(
        "Starting research: lookback=%d days, items=%d-%d, model=%s",
        args.lookback_days,
        args.min_items,
        args.max_items,
        args.model,
    )
    items, since, today = researcher.run(
        lookback_days=args.lookback_days,
        min_items=args.min_items,
        max_items=args.max_items,
        model=args.model,
    )
    logger.info("Got %d valid items", len(items))

    if not items:
        print("ERROR: no items returned by researcher", file=sys.stderr)
        return 1

    html = renderer.render(items, since, today)

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    preview_path = out_dir / "preview.html"
    preview_path.write_text(html, encoding="utf-8")
    logger.info("Preview written to %s (%d chars)", preview_path, len(html))

    if args.dry_run:
        print(f"Dry run complete. {len(items)} items. Open {preview_path} to review.")
        return 0

    emailer.send(html, today)
    print(f"Email sent to {os.environ['RECIPIENT_EMAIL']} with {len(items)} items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
