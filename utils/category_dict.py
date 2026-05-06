import ast
from pathlib import Path

from config.constants import CATEGORY_DICT


CONSTANTS_PATH = Path(__file__).resolve().parents[1] / "config" / "constants.py"


def get_category_pairs(category_dict=None) -> list[dict[str, str]]:
    """Return editable category/code pairs from literal CATEGORY_DICT entries."""
    source = category_dict or CATEGORY_DICT
    pairs: list[dict[str, str]] = []

    for code, name in source.items():
        normalized_code = str(code or "").strip()
        normalized_name = str(name or "").strip()
        if not normalized_code or not normalized_name:
            continue
        pairs.append({"name": normalized_name, "code": normalized_code})

    return pairs


def build_category_dict(category_pairs) -> dict[str, str]:
    """Build CATEGORY_DICT exactly from the submitted category/code pairs."""
    category_dict: dict[str, str] = {}
    seen_codes = set()

    for pair in category_pairs:
        name = str((pair or {}).get("name") or "").strip()
        code = str((pair or {}).get("code") or "").strip()

        if not name and not code:
            continue
        if not name or not code:
            raise ValueError("Each category row must include both a name and a 3-letter code.")
        if len(code) != 3 or not code.isalpha():
            raise ValueError(f"Category code '{code}' must be exactly 3 letters.")

        if code in seen_codes:
            raise ValueError(f"Category code '{code}' is duplicated.")

        seen_codes.add(code)
        category_dict[code] = name

    if not category_dict:
        raise ValueError("Add at least one category mapping.")

    return category_dict


def save_category_dict(category_pairs) -> dict[str, str]:
    """Persist category mappings into constants.py and update the in-memory lookup."""
    updated_dict = build_category_dict(category_pairs)
    constants_text = CONSTANTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(constants_text)

    target_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CATEGORY_DICT":
                    target_node = node
                    break
        if target_node:
            break

    if target_node is None:
        raise ValueError("CATEGORY_DICT was not found in config/constants.py.")

    lines = constants_text.splitlines()
    replacement = _format_category_dict(updated_dict).splitlines()
    lines[target_node.lineno - 1:target_node.end_lineno] = replacement
    CONSTANTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    CATEGORY_DICT.clear()
    CATEGORY_DICT.update(updated_dict)
    return updated_dict


def _format_category_dict(category_dict: dict[str, str]) -> str:
    lines = ["CATEGORY_DICT = {"]
    for key, value in category_dict.items():
        lines.append(f"    {key!r}: {value!r},")
    lines.append("}")
    return "\n".join(lines)
