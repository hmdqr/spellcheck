"""Language resolution and small persistence helpers for the Spellcheck addon."""

from __future__ import annotations

import os
import json
import globalVars
import languageHandler
import winUser

from .language_dictionary import get_all_possible_languages, list_installed_dictionaries


def get_input_language(thread_id: int) -> str:
    """Return current input language tag for the given thread id."""
    kbdlid = winUser.getKeyboardLayout(thread_id)
    windows_lcid = kbdlid & (2 ** 16 - 1)
    return languageHandler.windowsLCIDToLocaleName(windows_lcid)


def get_active_or_input_language(active_lang_tag: str | None, thread_id: int) -> str:
    """Return the active language if set; otherwise return the current input language."""
    return active_lang_tag or get_input_language(thread_id)


def get_installed_or_all_language_tags() -> list[str]:
    """Return installed dictionary tags if any; otherwise return all downloadable tags."""
    try:
        installed = [rec.get("tag") for rec in list_installed_dictionaries() if rec.get("tag")]
    except Exception:
        installed = []
    if installed:
        return sorted(set(installed))
    all_tags = get_all_possible_languages()
    return sorted(all_tags) if isinstance(all_tags, (set, list, tuple)) else list(all_tags)


def _state_path() -> str:
    # Store a tiny state file alongside other NVDA user config data
    return os.path.join(globalVars.appArgs.configPath, "spellcheck_state.json")


def load_active_lang_tag() -> str | None:
    try:
        with open(_state_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            val = data.get("activeLangTag")
            return val if isinstance(val, str) and val else None
    except Exception:
        return None


def save_active_lang_tag(tag: str | None) -> None:
    try:
        path = _state_path()
        data = {"activeLangTag": tag if isinstance(tag, str) and tag else None}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # Persistence is best-effort; ignore failures silently.
        pass
