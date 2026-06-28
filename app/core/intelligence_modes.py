"""Intelligence mode contract."""

from __future__ import annotations


INTELLIGENCE_MODES = {
    "local_auto": {
        "label": "Local automatico",
        "codex_required": False,
        "description": "Testa variacoes programadas sem usar IA externa.",
    },
    "codex_assisted": {
        "label": "Codex assisted",
        "codex_required": False,
        "description": "Usa Codex para propor alteracoes MQL5 avancadas com autorizacao explicita.",
    },
    "seeds_only": {
        "label": "Seeds only",
        "codex_required": False,
        "description": "Testa apenas robos-base incluidos.",
    },
}


def validate_intelligence_modes(supported: list[str], default_mode: str) -> None:
    missing = [mode for mode in supported if mode not in INTELLIGENCE_MODES]
    if missing:
        raise ValueError(f"Unknown intelligence modes: {missing}")
    if default_mode != "local_auto":
        raise ValueError("local_auto must be the default intelligence mode")


def report_defaults(mode: str) -> dict[str, object]:
    if mode not in INTELLIGENCE_MODES:
        raise ValueError(f"Unknown intelligence mode: {mode}")
    if mode == "codex_assisted":
        return {
            "intelligence_mode": mode,
            "codex_used": False,
            "codex_authorized": False,
            "mutation_mode": "codex_packet_only_until_authorized",
            "seed_family": "pending_user_authorization",
        }
    if mode == "seeds_only":
        return {
            "intelligence_mode": mode,
            "codex_used": False,
            "codex_authorized": False,
            "mutation_mode": "seed_replay_only",
            "seed_family": "included_base_seed",
        }
    return {
        "intelligence_mode": mode,
        "codex_used": False,
        "codex_authorized": False,
        "mutation_mode": "programmatic_local_mutation",
        "seed_family": "local_auto",
    }
