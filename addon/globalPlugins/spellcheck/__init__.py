"""
Spellcheck global plugin entry point and scripts.
The UI (dialogs/downloader) is in settings_dialog.py to keep things tidy.
"""

import tones
import wx
import api
import gui
import ui
import globalVars
import globalPluginHandler
import queueHandler
import eventHandler
import textInfos
import languageHandler
import winUser
import NVDAObjects.behaviors
from contextlib import suppress
from scriptHandler import script
from logHandler import log

from .helpers import play_sound
from .spellcheck_ui import SpellCheckMenu, SCRCAT__SPELLCHECK
from .language_dictionary import (
    set_enchant_language_dictionaries_directory,
    get_all_possible_languages,
    get_enchant_language_dictionary,
    LanguageDictionaryNotAvailable,
    LanguageDictionaryDownloadable,
    MultipleDownloadableLanguagesFound,
)
from .settings_dialog import SpellcheckSettingsDialog, LanguageChoiceDialog, LanguageDictionaryDownloader

import addonHandler
addonHandler.initTranslation()

# Ensure '_' is available for translations even in static analysis.
try:
    _  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    import gettext as _gettext
    _ = _gettext.gettext


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_enchant_language_dictionaries_directory()
        self._active_spellcheck_language = None
        # Add menu item under Tools after GUI is ready
        wx.CallAfter(self._addToolsMenu)

    def _addToolsMenu(self):
        try:
            toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
            self._settingsMenuItem = toolsMenu.Append(wx.ID_ANY, _("Spellcheck settings"))
            gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onOpenSettings, self._settingsMenuItem)
        except Exception:
            # Log for diagnostics but avoid crashing the plugin
            log.exception("Failed to add Spellcheck settings to Tools menu")

    def on_language_variance_download(self, lang_tag):
        wx.CallAfter(LanguageDictionaryDownloader(lang_tag, ask_user=False).download)

    def on_user_chosen_language(self, lang_tag):
        self._active_spellcheck_language = lang_tag
        self.obtain_language_dictionary(lang_tag)

    def onOpenSettings(self, evt=None):
        dlg = SpellcheckSettingsDialog()
        gui.runScriptModalDialog(dlg)

    @script(
        gesture="kb:nvda+alt+control+s",
        # translators: appears in the NVDA input help.
        description=_("Opens the Spellcheck settings dialog"),
        category=SCRCAT__SPELLCHECK,
    )
    def script_open_spellcheck_settings(self, gesture):
        self.onOpenSettings()

    @script(
        gesture="kb:nvda+alt+shift+s",
        # translators: appears in the NVDA input help.
        description=(
            _("Checks spelling errors for the selected text using the current input language")
        ),
        category=SCRCAT__SPELLCHECK,
    )
    def script_spellcheck_text(self, gesture):
        text = self.getSelectedText()
        if not text:
            return
        if self._active_spellcheck_language is None:
            spellcheck_language = self.get_input_language(
                api.getFocusObject().windowThreadID
            )
        else:
            spellcheck_language = self._active_spellcheck_language
        self.spellcheck(spellcheck_language, text)

    @script(
        gesture="kb:nvda+alt+shift+l",
        # translators: appears in the NVDA input help.
        description=(
            _(
                "Toggles the method used in determining the language for spellchecking: user-chosen versus current input language"
            )
        ),
        category=SCRCAT__SPELLCHECK,
    )
    def script_toggle_user_chosen_spellcheck_language(self, gesture):
        if getattr(globalVars, "LANGUAGE_DIALOG_SHOWN", False):
            queueHandler.queueFunction(
                queueHandler.eventQueue,
                ui.message,
                # Translators: spoken message when the dialog is already open
                _("Dialog is already open")
            )
            return
        if self._active_spellcheck_language is None:
            lang_choice_dialog = LanguageChoiceDialog(
                get_all_possible_languages(),
                gui.mainFrame,
                # Translators: message of a dialog containing language choices
                _("Please choose the language you want to use for spellchecking."),
                # Translators: title of a dialog containing a list of languages
                _("Choose Spellcheck Language"),
            )
            gui.runScriptModalDialog(
                lang_choice_dialog,
                self.on_user_chosen_language,
            )
        else:
            self._active_spellcheck_language = None
            # Translators: spoken message when toggling the way the spellcheck language is determined
            queueHandler.queueFunction(
                queueHandler.eventQueue,
                ui.message,
                _("Using the active Input language for spellchecking"),
            )

    def spellcheck(self, language_tag, text_to_spellcheck):
        language_dictionary = self.obtain_language_dictionary(language_tag)
        if not language_dictionary:
            return
        # Create our fake menu object
        misspellingsMenu = SpellCheckMenu(
            # translators: the name of the menu that shows up when the addon is being activated.
            name=_("Spelling Errors"),
            language_dictionary=language_dictionary,
            text_to_process=text_to_spellcheck,
        )
        if not misspellingsMenu.items:
            # translators: announced when there are no spelling errors in a selected text.
            ui.message("No spelling mistakes")
            return
        eventHandler.queueEvent("gainFocus", misspellingsMenu)
        queueHandler.queueFunction(
            queueHandler.eventQueue,
            play_sound,
            "menu_open"
        )

    def obtain_language_dictionary(self, language_tag):
        try:
            return get_enchant_language_dictionary(language_tag)
        except MultipleDownloadableLanguagesFound as e:
            choice_dialog = LanguageChoiceDialog(
                e.available_variances,
                gui.mainFrame,
                # Translators: message of a dialog containing language choices
                _(
                    "Dialects found for language {lang}.\nPlease select the one you want to download."
                ).format(lang=languageHandler.getLanguageDescription(e.language)),
                # Translators: title of a dialog containing a list of languages
                _("Dialects Found"),
            )
            gui.runScriptModalDialog(choice_dialog, self.on_language_variance_download)
        except LanguageDictionaryDownloadable as e:
            wx.CallAfter(LanguageDictionaryDownloader(e.language).download)
        except LanguageDictionaryNotAvailable as e:
            lang = languageHandler.getLanguageDescription(e.language)
            if lang is None:
                lang = e.language
            queueHandler.queueFunction(
                queueHandler.eventQueue,
                ui.message,
                _("Language dictionary for language {lang} is not available.").format(
                    lang=lang
                ),
            )
        return False

    @staticmethod
    def get_input_language(thread_id):
        kbdlid = winUser.getKeyboardLayout(thread_id)
        windows_lcid = kbdlid & (2 ** 16 - 1)
        return languageHandler.windowsLCIDToLocaleName(windows_lcid)

    @staticmethod
    def getSelectedText() -> str:
        """Retrieve the selected text."""
        obj = api.getFocusObject()
        # Restrict the selection to editable text only
        if not isinstance(obj, NVDAObjects.behaviors.EditableText):
            # translators: the message is announced when there is no text is selected.
            queueHandler.queueFunction(
                queueHandler.eventQueue,
                ui.message,
                _("Spellchecking is not supported here"),
            )
            return
        treeInterceptor = obj.treeInterceptor
        if hasattr(treeInterceptor, "TextInfo") and not treeInterceptor.passThrough:
            obj = treeInterceptor
        text = ""
        with suppress(RuntimeError, NotImplementedError):
            info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
            # Do not strip whitespace; users expect exact selection including newlines/spaces.
            text = info.text
        if not text:
            # translators: the message is announced when there is no text is selected.
            queueHandler.queueFunction(
                queueHandler.eventQueue, ui.message, _("No text is selected")
            )
        return text
