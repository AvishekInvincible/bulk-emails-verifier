thonimport json
import logging
from typing import Any, List, Dict

logger = logging.getLogger(__name__)

def results_to_json(results: List[Dict[str, Any]]) -> str:
    """
    Convert a list of result dictionaries into a pretty-printed JSON string.
    """
    logger.debug("Serializing %d result(s) to JSON.", len(results))
    return json.dumps(results, indent=2, ensure_ascii=False)

def save_json_to_file(json_str: str, path: str) -> None:
    """
    Write a JSON string to the given file path.
    """
    logger.debug("Saving JSON output to %s", path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_str)
    logger.info("JSON output successfully written to %s", path)