# coding: utf-8

# Copyright (c) 2021 Blind Pandas Team
# This file is covered by the GNU General Public License.

import sys
import os
import contextlib
from nvwave import playWaveFile


PLUGIN_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
LIBS_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "libs")
DATA_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "data")
SOUNDS_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "sounds")


@contextlib.contextmanager
def import_bundled_library():
    # Append (not prepend) to avoid shadowing stdlib modules on newer Python/NVDA.
    # This ensures we still find third-party packages (e.g., enchant, httpx)
    # without accidentally overriding standard library modules such as asyncio.
    sys.path.append(LIBS_DIRECTORY)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(LIBS_DIRECTORY)


def play_sound(name):
    with contextlib.suppress(Exception):
        playWaveFile(os.path.join(SOUNDS_DIRECTORY, f"{name}.wav"))
