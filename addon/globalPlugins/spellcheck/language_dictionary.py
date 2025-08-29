# coding: utf-8

# Copyright (c) 2021 Blind Pandas Team
# This file is covered by the GNU General Public License.

import math
import os
import globalVars
import languageHandler
from io import BytesIO
from functools import partial
from logHandler import log
from .helpers import import_bundled_library, DATA_DIRECTORY


with import_bundled_library():
    # Suppress DeprecationWarning from Python stdlib 'cgi' module imported by older httpx versions.
    # Python 3.12 warns that 'cgi' is deprecated and will be removed in 3.13.
    # This filter targets only the 'cgi' module to avoid hiding other deprecations.
    import warnings  # noqa: E402
    warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"^cgi$")
    import enchant  # noqa: E402
    import httpx  # noqa: E402
    from concurrent.futures import ThreadPoolExecutor  # noqa: E402


# Constants
DICT_GITHUB_API_URL = "https://api.github.com/repos/LibreOffice/dictionaries/contents/{lang_tag}?ref=master"
DICT_GITHUB_COMMITS_API_URL = "https://api.github.com/repos/LibreOffice/dictionaries/commits?path={lang_tag}&sha=master&per_page=1"
DICTIONARY_FILE_EXTS = {
    ".dic",
    ".aff",
}
THREAD_POOL_EXECUTOR = ThreadPoolExecutor()
SPELLCHECK_DICTIONARIES_DIRECTORY = os.path.join(
    globalVars.appArgs.configPath, "spellcheck_dictionaries"
)
with open(os.path.join(DATA_DIRECTORY, "downloadable_languages.txt"), "r") as file:
    DOWNLOADABLE_LANGUAGES = [tag.strip() for tag in file if tag.strip()]

# Metadata file to store installed dictionary versions (latest known commit sha)
def _get_hunspell_dir() -> str:
    return os.path.join(SPELLCHECK_DICTIONARIES_DIRECTORY, "hunspell")


def _get_meta_path() -> str:
    return os.path.join(_get_hunspell_dir(), "_meta.json")


def _load_meta() -> dict:
    import json
    p = _get_meta_path()
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_meta(meta: dict) -> None:
    import json
    d = _get_hunspell_dir()
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(_get_meta_path(), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def get_local_dictionary_version(tag: str) -> str | None:
    meta = _load_meta()
    info = meta.get(tag)
    if not info:
        return None
    return info.get("commit")


def set_local_dictionary_version(tag: str, commit: str | None) -> None:
    meta = _load_meta()
    meta[tag] = {"commit": commit}
    _save_meta(meta)


class LanguageDictionaryNotAvailable(LookupError):
    """Raised when the given language has no dictionary."""

    def __init__(self, language):
        self.language = language


class LanguageDictionaryDownloadable(LanguageDictionaryNotAvailable):
    """Raised if the language dictionary is unavailable locally, but available for download."""


class MultipleDownloadableLanguagesFound(LanguageDictionaryDownloadable):
    """Raised if more than one variant are available for download."""

    def __init__(self, language, available_variances, *args, **kwargs):
        super().__init__(language, *args, **kwargs)
        self.available_variances = available_variances


def set_enchant_language_dictionaries_directory():
    if not os.path.isdir(SPELLCHECK_DICTIONARIES_DIRECTORY):
        os.mkdir(SPELLCHECK_DICTIONARIES_DIRECTORY)
    os.environ["ENCHANT_CONFIG_DIR"] = SPELLCHECK_DICTIONARIES_DIRECTORY


def _get_hunspell_dir() -> str:
    """Return the hunspell extraction directory where .dic/.aff live."""
    return os.path.join(SPELLCHECK_DICTIONARIES_DIRECTORY, "hunspell")


def list_installed_dictionaries(include_remote: bool = False):
    """List installed dictionary tags, size, and optional version info.

    Returns: list of dicts with keys: tag, size, localVersion, latestVersion, status
    status: "upToDate" | "updateAvailable" | "unknown"
    If include_remote is False, latestVersion and status may be omitted/unknown.
    """
    d = _get_hunspell_dir()
    if not os.path.isdir(d):
        return []
    entries = {}
    try:
        for name in os.listdir(d):
            base, ext = os.path.splitext(name)
            if ext.lower() not in DICTIONARY_FILE_EXTS:
                continue
            full = os.path.join(d, name)
            size = 0
            with open(full, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
            entries.setdefault(base, {"need": set([".dic", ".aff"]), "size": 0})
            entries[base]["need"].discard(ext.lower())
            entries[base]["size"] += size
    except Exception:
        return []
    result = []
    for tag, info in entries.items():
        if info["need"]:
            continue
        localCommit = get_local_dictionary_version(tag)
        rec = {"tag": tag, "size": info["size"], "localVersion": localCommit}
        if include_remote and tag in DOWNLOADABLE_LANGUAGES:
            try:
                latest = get_latest_remote_dictionary_version(tag)
                rec["latestVersion"] = latest
                if localCommit and latest and localCommit != latest:
                    rec["status"] = "updateAvailable"
                elif localCommit and latest and localCommit == latest:
                    rec["status"] = "upToDate"
                else:
                    rec["status"] = "unknown"
            except Exception:
                rec["status"] = "unknown"
        result.append(rec)
    result.sort(key=lambda x: x["tag"])
    return result


def list_languages_status(include_remote: bool = False):
    """Return friendly status for all downloadable languages.

    Each record includes:
      - tag: language tag
      - name: localized language description (fallback to tag)
      - installed: bool
      - size: int bytes (0 if not installed)
      - localVersion: optional str (commit sha)
      - latestVersion: optional str (commit sha, when include_remote)
      - status: one of: notInstalled | upToDate | updateAvailable | unknown
    """
    installed_map = {rec["tag"]: rec for rec in list_installed_dictionaries(include_remote=include_remote)}
    items = []
    for tag in DOWNLOADABLE_LANGUAGES:
        name = languageHandler.getLanguageDescription(tag) or tag
        inst = installed_map.get(tag)
        if inst:
            rec = {
                "tag": tag,
                "name": name,
                "installed": True,
                "size": inst.get("size", 0),
                "localVersion": inst.get("localVersion"),
            }
            if include_remote:
                rec["latestVersion"] = inst.get("latestVersion")
                rec["status"] = inst.get("status") or ("unknown" if inst.get("localVersion") else "unknown")
            items.append(rec)
        else:
            # For not installed languages, avoid remote network calls on the UI thread.
            rec = {
                "tag": tag,
                "name": name,
                "installed": False,
                "size": 0,
                "localVersion": None,
            }
            if include_remote:
                rec["latestVersion"] = None
                rec["status"] = "notInstalled"
            items.append(rec)
    items.sort(key=lambda r: (r["name"].lower(), r["tag"]))
    return items


def get_latest_remote_dictionary_version(lang_tag: str) -> str | None:
    """Return latest commit sha for lang folder on master branch via GitHub API."""
    url = DICT_GITHUB_COMMITS_API_URL.format(lang_tag=lang_tag)
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list) and data:
        sha = data[0].get("sha")
        return sha
    return None


def get_latest_remote_versions(tags: list[str]) -> dict[str, str | None]:
    """Return a mapping of tag->latest commit sha (or None) for the given tags.

    This performs network requests and should be called off the UI thread.
    """
    results: dict[str, str | None] = {}
    with httpx.Client(timeout=10) as client:
        for tag in tags:
            try:
                url = DICT_GITHUB_COMMITS_API_URL.format(lang_tag=tag)
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
                sha = data[0].get("sha") if isinstance(data, list) and data else None
                results[tag] = sha
            except Exception:
                results[tag] = None
    return results


def remove_installed_dictionary(tag: str) -> bool:
    """Remove .dic/.aff files for the given tag. Returns True if any file removed."""
    d = _get_hunspell_dir()
    removed = False
    for ext in (".dic", ".aff"):
        p = os.path.join(d, f"{tag}{ext}")
        if os.path.isfile(p):
            try:
                os.remove(p)
                removed = True
            except Exception:
                pass
    if removed:
        try:
            set_local_dictionary_version(tag, None)
        except Exception:
            pass
    return removed


def get_all_possible_languages():
    return set(DOWNLOADABLE_LANGUAGES)


def get_enchant_language_dictionary(lang_tag):
    try:
        return enchant.request_dict(lang_tag)
    except enchant.errors.DictNotFoundError:
        if lang_tag in DOWNLOADABLE_LANGUAGES:
            raise LanguageDictionaryDownloadable(lang_tag)
        elif "_" in lang_tag:
            return get_enchant_language_dictionary(lang_tag.split("_")[0])
        else:
            if len(lang_tag) == 2:
                available_variances = [
                    downloadable_lang
                    for downloadable_lang in DOWNLOADABLE_LANGUAGES
                    if downloadable_lang.split("_")[0] == lang_tag
                ]
                if available_variances:
                    raise MultipleDownloadableLanguagesFound(
                        language=lang_tag, available_variances=available_variances
                    )
    raise LanguageDictionaryNotAvailable(lang_tag)


def download_language_dictionary(lang_tag, progress_callback, done_callback):
    if lang_tag not in DOWNLOADABLE_LANGUAGES:
        raise ValueError(f"Language {lang_tag} is not available for download")
    THREAD_POOL_EXECUTOR.submit(
        _do_download__and_extract_lang_dictionary, lang_tag, progress_callback
    ).add_done_callback(partial(_done_callback, done_callback))


def get_language_dictionary_download_info(lang_tag):
    directory_listing = httpx.get(DICT_GITHUB_API_URL.format(lang_tag=lang_tag)).json()
    return {
        entry["name"]: (entry["download_url"], entry["size"])
        for entry in directory_listing
        if os.path.splitext(entry["name"])[-1] in DICTIONARY_FILE_EXTS
    }


def _do_download__and_extract_lang_dictionary(lang_tag, progress_callback):
    download_info = get_language_dictionary_download_info(lang_tag)
    name_to_buffer = {}
    total_size = sum(filesize for (n, (u, filesize)) in download_info.items())
    downloaded_til_now = 0
    for (filename, (download_url, file_size)) in download_info.items():
        downloaded_this_file = 0
        with httpx.Client() as client:
            with client.stream("GET", download_url) as response:
                file_buffer = BytesIO()
                for data in response.iter_bytes():
                    file_buffer.write(data)
                    downloaded_til_now += len(data)
                    downloaded_this_file += len(data)
                    progress = math.floor((downloaded_til_now / total_size) * 100)
                    # Overall progress as an int (backward compatible)
                    try:
                        progress_callback(progress)
                    except TypeError:
                        # In case caller expects dict-only, ignore
                        pass
                    # Per-file progress as a dict {file, progress}
                    try:
                        file_progress = 0 if file_size == 0 else math.floor((downloaded_this_file / file_size) * 100)
                        progress_callback({"file": filename, "progress": file_progress})
                    except TypeError:
                        # In case caller expects int-only, ignore
                        pass
                file_buffer.seek(0)
                name_to_buffer[filename] = file_buffer
    # Now copy the downloaded file to the destination
    hunspell_extraction_directory = os.path.join(
        SPELLCHECK_DICTIONARIES_DIRECTORY, "hunspell"
    )
    if not os.path.isdir(hunspell_extraction_directory):
        os.mkdir(hunspell_extraction_directory)
    for (filename, file_buffer) in name_to_buffer.items():
        full_file_path = os.path.join(hunspell_extraction_directory, filename)
        with open(full_file_path, "wb") as output_file:
            output_file.write(file_buffer.getvalue())
    # record local version as latest remote commit
    try:
        latest = get_latest_remote_dictionary_version(lang_tag)
        set_local_dictionary_version(lang_tag, latest)
    except Exception:
        set_local_dictionary_version(lang_tag, None)


def _done_callback(done_callback, future):
    if done_callback is None:
        return
    try:
        result = future.result()
        done_callback(None)
    except httpx.HTTPError:
        done_callback(ConnectionError("Failed to get language dictionary"))
    except Exception as e:
        done_callback(e)
