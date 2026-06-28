#!/usr/bin/env python3
"""Grand MVP Factory command line utility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FACTORY_DIR = ROOT / "factory"
QUEUE_PATH = FACTORY_DIR / "mvp_queue.json"
STATUS_PATH = FACTORY_DIR / "mvp_status.json"
PROMPT_TEMPLATE_PATH = FACTORY_DIR / "templates" / "grand_mvp_prompt_template.md"

REQUIRED_FIELDS = {
    "id",
    "title",
    "type",
    "status",
    "priority",
    "objective",
    "allowed_scope",
    "forbidden_scope",
    "expected_files",
    "validation_commands",
    "done_criteria",
    "risk_flags",
    "next_handoff",
}

VALID_STATUSES = {"planned", "active", "done", "blocked", "paused"}
REQUIRED_FORBIDDEN_TERMS = {"ea-xau", "PayoffGrid", "ONPN11"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_queue() -> list[dict[str, Any]]:
    queue = load_json(QUEUE_PATH)
    if not isinstance(queue, list):
        raise ValueError("mvp_queue.json must contain a list")
    return queue


def validate_queue(queue: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    for item in queue:
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"{item.get('id', '<missing id>')} missing fields: {sorted(missing)}")
        if item["id"] in ids:
            raise ValueError(f"Duplicate MVP id: {item['id']}")
        ids.add(item["id"])
        if item["status"] not in VALID_STATUSES:
            raise ValueError(f"{item['id']} has invalid status: {item['status']}")
        forbidden_text = " ".join(str(value) for value in item["forbidden_scope"])
        for term in REQUIRED_FORBIDDEN_TERMS:
            if term not in forbidden_text:
                raise ValueError(f"{item['id']} forbidden_scope does not mention {term}")
    if len(queue) != 10:
        raise ValueError(f"Expected 10 MVPs, found {len(queue)}")


def find_mvp(queue: list[dict[str, Any]], mvp_id: str) -> dict[str, Any]:
    for item in queue:
        if item["id"] == mvp_id:
            return item
    raise KeyError(f"MVP not found: {mvp_id}")


def next_mvp(queue: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in queue:
        if item["status"] in {"planned", "active"}:
            return item
    return None


def render_list(values: list[Any]) -> str:
    return "\n".join(f"- {value}" for value in values)


def render_prompt(item: dict[str, Any]) -> str:
    template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = template
    for key, value in item.items():
        if isinstance(value, list):
            replacement = render_list(value)
        else:
            replacement = str(value)
        rendered = rendered.replace("{" + key + "}", replacement)
    return rendered


def mark_status(mvp_id: str, status: str) -> dict[str, str]:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    statuses = load_json(STATUS_PATH)
    if not isinstance(statuses, dict):
        raise ValueError("mvp_status.json must contain an object")
    if mvp_id not in statuses:
        raise KeyError(f"MVP not found in status file: {mvp_id}")
    statuses[mvp_id] = status
    write_json(STATUS_PATH, statuses)
    return statuses


def self_test() -> str:
    queue = load_queue()
    validate_queue(queue)
    prompt = render_prompt(find_mvp(queue, "MVP-001"))
    if "Desktop Navigation v2" not in prompt:
        raise AssertionError("Prompt rendering failed for MVP-001")
    return "mvp_factory_self_test_passed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 Robot Lab Grand MVP Factory")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--show")
    parser.add_argument("--generate-prompt")
    parser.add_argument("--mark-status", nargs=2, metavar=("MVP_ID", "STATUS"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    queue = load_queue()
    validate_queue(queue)

    if args.self_test:
        print(self_test())
        return 0
    if args.list:
        for item in queue:
            print(f"{item['id']} | {item['status']} | {item['priority']} | {item['title']}")
        return 0
    if args.next:
        item = next_mvp(queue)
        if item is None:
            print("NO_NEXT_MVP")
        else:
            print(f"{item['id']} | {item['title']} | {item['status']}")
        return 0
    if args.show:
        print(json.dumps(find_mvp(queue, args.show), indent=2, sort_keys=True))
        return 0
    if args.generate_prompt:
        print(render_prompt(find_mvp(queue, args.generate_prompt)))
        return 0
    if args.mark_status:
        mvp_id, status = args.mark_status
        mark_status(mvp_id, status)
        print(f"{mvp_id} status set to {status}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
