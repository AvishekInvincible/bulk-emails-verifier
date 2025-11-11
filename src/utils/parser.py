thonimport logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def load_emails_from_file(path: str, limit: Optional[int] = None) -> List[str]:
    """
    Load emails from a plain text file, one per line.
    Lines starting with '#' are treated as comments and ignored.
    Empty lines are skipped.
    """
    emails: List[str] = []
    logger.debug("Loading emails from %s", path)

    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            emails.append(line)
            if limit is not None and len(emails) >= limit:
                logger.debug(
                    "Reached email limit %s while reading %s (line %s).",
                    limit,
                    path,
                    line_number,
                )
                break

    logger.info("Loaded %d email(s) from %s", len(emails), path)
    return emails