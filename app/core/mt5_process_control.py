"""MT5 process lifecycle policy for real local runs.

The close policy is intentionally conservative: MT5 Robot Lab may close only
the terminal process it started for a gated real run. If a terminal was already
open before the app-owned run, the app records manual close as required instead
of terminating an external user session.
"""

from __future__ import annotations

import csv
import subprocess
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path

from app.core.mt5_detection import redact_public_path


MT5_TERMINAL_PROCESS_NAMES = {"terminal64.exe", "terminal.exe"}


@dataclass(frozen=True)
class MT5ProcessInfo:
    pid: int | None = None
    name: str = "terminal64.exe"
    owned_by_app: bool = False
    already_running: bool = False
    path_sanitized: str = ""


@dataclass(frozen=True)
class MT5ClosePolicy:
    mt5_close_policy: str = "always_after_real_run"
    close_external_processes: bool = False
    timeout_seconds: int = 10


@dataclass(frozen=True)
class MT5CloseResult:
    mt5_close_policy: str
    mt5_close_attempted: bool
    mt5_closed_after_run: bool
    mt5_close_method: str
    mt5_close_error: str
    mt5_process_owned_by_app: bool
    mt5_external_process_detected: bool
    manual_close_required: bool


def default_mt5_close_policy() -> MT5ClosePolicy:
    """Return the default policy for every gated real MT5 run."""

    return MT5ClosePolicy()


def _clean_error(message: object) -> str:
    text = str(message or "").strip()
    return redact_public_path(text) if text else ""


def _default_close_result(
    process_info: MT5ProcessInfo | None,
    policy: MT5ClosePolicy,
    *,
    attempted: bool,
    closed: bool,
    method: str,
    error: object = "",
    manual_close_required: bool = False,
) -> MT5CloseResult:
    owned = bool(process_info and process_info.owned_by_app)
    external = bool(process_info and not process_info.owned_by_app and process_info.already_running)
    return MT5CloseResult(
        mt5_close_policy=policy.mt5_close_policy,
        mt5_close_attempted=attempted,
        mt5_closed_after_run=closed,
        mt5_close_method=method,
        mt5_close_error=_clean_error(error),
        mt5_process_owned_by_app=owned,
        mt5_external_process_detected=external,
        manual_close_required=manual_close_required,
    )


def find_mt5_processes() -> list[MT5ProcessInfo]:
    """List visible MT5 terminal processes without closing or modifying them."""

    discovered: list[MT5ProcessInfo] = []
    for process_name in sorted(MT5_TERMINAL_PROCESS_NAMES):
        try:
            completed = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {process_name}"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0:
            continue
        for row in csv.reader(StringIO(completed.stdout)):
            if len(row) < 2:
                continue
            image_name = row[0].strip()
            if image_name.upper() == "INFO:" or image_name.lower() not in MT5_TERMINAL_PROCESS_NAMES:
                continue
            try:
                pid = int(row[1])
            except ValueError:
                pid = None
            discovered.append(
                MT5ProcessInfo(
                    pid=pid,
                    name=image_name,
                    owned_by_app=False,
                    already_running=True,
                    path_sanitized="",
                )
            )
    return discovered


def verify_mt5_closed(process_info: MT5ProcessInfo) -> bool:
    """Return true when the specific PID is no longer visible."""

    if process_info.pid is None:
        return False
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH", "/FI", f"PID eq {process_info.pid}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = completed.stdout.lower()
    return str(process_info.pid) not in output or "no tasks are running" in output


def close_terminal_process(process_info: MT5ProcessInfo) -> MT5CloseResult:
    """Close an app-owned MT5 terminal process and return a sanitized summary."""

    policy = default_mt5_close_policy()
    if not process_info.owned_by_app:
        return _default_close_result(
            process_info,
            policy,
            attempted=False,
            closed=False,
            method="external_process_not_closed",
            manual_close_required=True,
        )
    if process_info.pid is None:
        return _default_close_result(
            process_info,
            policy,
            attempted=True,
            closed=False,
            method="owned_process_no_pid",
            manual_close_required=True,
            error="missing process id",
        )
    try:
        completed = subprocess.run(
            ["taskkill", "/PID", str(process_info.pid), "/T"],
            check=False,
            capture_output=True,
            text=True,
            timeout=policy.timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _default_close_result(
            process_info,
            policy,
            attempted=True,
            closed=False,
            method="taskkill_failed",
            error=exc,
            manual_close_required=True,
        )
    closed = verify_mt5_closed(process_info)
    return _default_close_result(
        process_info,
        policy,
        attempted=True,
        closed=closed,
        method="taskkill_pid_tree",
        error=completed.stderr if completed.returncode != 0 and not closed else "",
        manual_close_required=not closed,
    )


def close_mt5_after_run(
    process_info: MT5ProcessInfo | None,
    policy: MT5ClosePolicy | None = None,
) -> MT5CloseResult:
    """Apply close-after-run policy after a real MT5 attempt finishes."""

    close_policy = policy or default_mt5_close_policy()
    if process_info is None:
        return _default_close_result(
            None,
            close_policy,
            attempted=False,
            closed=False,
            method="no_process_info",
            manual_close_required=False,
        )
    if not process_info.owned_by_app:
        return _default_close_result(
            process_info,
            close_policy,
            attempted=False,
            closed=False,
            method="external_process_not_closed",
            manual_close_required=True,
        )
    if process_info.pid is not None and verify_mt5_closed(process_info):
        return _default_close_result(
            process_info,
            close_policy,
            attempted=True,
            closed=True,
            method="owned_process_already_closed",
        )
    if process_info.pid is None:
        return _default_close_result(
            process_info,
            close_policy,
            attempted=True,
            closed=False,
            method="owned_process_no_pid",
            error="missing process id",
            manual_close_required=True,
        )
    result = close_terminal_process(process_info)
    if result.mt5_close_policy == close_policy.mt5_close_policy:
        return result
    return MT5CloseResult(**{**asdict(result), "mt5_close_policy": close_policy.mt5_close_policy})


def make_mt5_close_summary(close_result: MT5CloseResult | dict[str, object] | None) -> dict[str, object]:
    """Return the public-safe close lifecycle fields for manifests and reports."""

    defaults = {
        "mt5_close_policy": default_mt5_close_policy().mt5_close_policy,
        "mt5_close_attempted": False,
        "mt5_closed_after_run": False,
        "mt5_close_method": "not_applicable",
        "mt5_close_error": "",
        "mt5_process_owned_by_app": False,
        "mt5_external_process_detected": False,
        "manual_close_required": False,
    }
    if close_result is None:
        close_result = _default_close_result(
            None,
            default_mt5_close_policy(),
            attempted=False,
            closed=False,
            method="not_applicable",
        )
    if isinstance(close_result, MT5CloseResult):
        return asdict(close_result)
    source = dict(close_result)
    return {key: source.get(key, default) for key, default in defaults.items()}


def make_app_owned_process_info(pid: int | None, terminal_path: str) -> MT5ProcessInfo:
    """Create sanitized process metadata for a terminal started by this app."""

    return MT5ProcessInfo(
        pid=pid,
        name=Path(terminal_path).name or "terminal64.exe",
        owned_by_app=True,
        already_running=False,
        path_sanitized=redact_public_path(terminal_path),
    )
