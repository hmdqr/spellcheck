# coding: utf-8

"""
Settings UI and related dialogs for the Spellcheck add-on.
Includes:
- LanguageChoiceDialog: choose a dialect/language
- SpellcheckSettingsDialog: manage dictionaries (install/update/delete)
- LanguageDictionaryDownloader: download/install/update flow with progress
"""

import wx
import gui
import ui
import languageHandler
from logHandler import log
from contextlib import suppress

from .language_dictionary import (
    list_languages_status,
    get_latest_remote_versions,
    remove_installed_dictionary,
    download_language_dictionary,
)

import addonHandler
addonHandler.initTranslation()

# Ensure '_' is available for translations even in static analysis.
try:
    _  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    import gettext as _gettext
    _ = _gettext.gettext


class LanguageChoiceDialog(wx.SingleChoiceDialog):
    def __init__(self, language_tags, *args, **kwargs):
        self.language_tags = tuple(sorted(language_tags))
        choices = [
            languageHandler.getLanguageDescription(l) for l in self.language_tags
        ]
        kwargs["choices"] = choices
        super().__init__(*args, **kwargs)

    def ShowModal(self):
        import globalVars
        globalVars.LANGUAGE_DIALOG_SHOWN = True
        retval = super().ShowModal()
        globalVars.LANGUAGE_DIALOG_SHOWN = False
        if retval == wx.ID_OK:
            return self.language_tags[self.GetSelection()]


class SpellcheckSettingsDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super().__init__(parent=gui.mainFrame, title=_("Spellcheck settings"), *args, **kwargs)
        panel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        # Filter controls
        filterSizer = wx.BoxSizer(wx.HORIZONTAL)
        filterSizer.Add(wx.StaticText(panel, label=_("Filter:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.filterChoice = wx.Choice(panel, choices=[
            _("All"), _("Installed"), _("Not installed"), _("Has updates")
        ])
        self.filterChoice.SetSelection(0)
        filterSizer.Add(self.filterChoice, 0)
        panelSizer.Add(filterSizer, 0, wx.ALL, 10)

        # List control with two columns
        self.listCtrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.listCtrl.InsertColumn(0, _("Language"), width=320)
        self.listCtrl.InsertColumn(1, _("Status"), width=460)
        panelSizer.Add(self.listCtrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        # Buttons
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.refreshBtn = wx.Button(panel, label=_("Refresh"))
        self.installBtn = wx.Button(panel, label=_("Install"))
        self.updateBtn = wx.Button(panel, label=_("Update"))
        self.deleteBtn = wx.Button(panel, label=_("Delete"))
        self.closeBtn = wx.Button(panel, id=wx.ID_CLOSE, label=_("Close"))
        btnSizer.Add(self.refreshBtn)
        btnSizer.AddSpacer(8)
        btnSizer.Add(self.installBtn)
        btnSizer.AddSpacer(8)
        btnSizer.Add(self.updateBtn)
        btnSizer.AddSpacer(8)
        btnSizer.Add(self.deleteBtn)
        btnSizer.AddStretchSpacer()
        btnSizer.Add(self.closeBtn)
        panelSizer.Add(btnSizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(panelSizer)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        dlgSizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(dlgSizer)
        self.CentreOnScreen()

        # Internal state
        self._items = []
        self._rows = []  # list index -> tag
        self._filterMode = 'all'

        # Bindings
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.onRefresh)
        self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
        self.updateBtn.Bind(wx.EVT_BUTTON, self.onUpdate)
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.onDelete)
        self.closeBtn.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
        self.filterChoice.Bind(wx.EVT_CHOICE, self.onFilterChanged)
        self.listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectionChanged)

        self.populate()

    def populate(self):
        self.listCtrl.DeleteAllItems()
        self._rows = []
        # Get local snapshot without remote calls
        self._items = list_languages_status(include_remote=False)
        # Render initial view
        self._refresh_list()
        # Now asynchronously fetch remote versions for installed tags and update rows
        local_versions = {rec['tag']: rec.get('localVersion') for rec in self._items if rec.get('installed')}
        self._update_remote_status_async(local_versions)

    def _refresh_list(self):
        self.listCtrl.DeleteAllItems()
        self._rows = []
        currentFilter = self._filterMode
        for rec in self._items:
            installed = rec.get("installed", False)
            statusKey = rec.get("status") or ("notInstalled" if not installed else "checking")
            # Apply filter
            if currentFilter == "installed" and not installed:
                continue
            if currentFilter == "notInstalled" and installed:
                continue
            if currentFilter == "updates" and statusKey != "updateAvailable":
                continue
            nameText = f"{rec['name']} ({rec['tag']})"
            idx = self.listCtrl.InsertItem(self.listCtrl.GetItemCount(), nameText)
            self._rows.append(rec['tag'])
            localVer = rec.get("localVersion")
            latestVer = rec.get("latestVersion")
            size = rec.get("size", 0)
            sizeMB = f"{(size/(1024*1024)):.1f} MB" if size else None
            if not installed:
                msg = _("Not installed.")
            elif statusKey == "upToDate":
                base = _("Installed")
                msg = f"{base} — " + _("Up to date")
            elif statusKey == "updateAvailable":
                base = _("Installed")
                msg = f"{base} — " + _("Update available")
            else:
                base = _("Installed")
                msg = f"{base} — " + _("Checking for updates…")
            if sizeMB:
                msg += f" — {sizeMB}"
            self.listCtrl.SetItem(idx, 1, msg)
        self._updateButtons()

    def _update_remote_status_async(self, local_versions: dict[str, str | None]):
        import threading

        def worker():
            tags = list(local_versions.keys())
            if not tags:
                return
            latest_map = get_latest_remote_versions(tags)

            def apply_updates():
                # Update our data model, then refresh the view with current filter
                tags_set = set(local_versions.keys())
                for rec in self._items:
                    if rec.get('tag') in tags_set:
                        localVer = rec.get('localVersion')
                        latest = latest_map.get(rec['tag'])
                        rec['latestVersion'] = latest
                        if localVer and latest:
                            rec['status'] = 'upToDate' if localVer == latest else 'updateAvailable'
                        else:
                            rec['status'] = 'unknown'
                self._refresh_list()

            wx.CallAfter(apply_updates)

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def onFilterChanged(self, evt):
        idx = self.filterChoice.GetSelection()
        self._filterMode = {0: 'all', 1: 'installed', 2: 'notInstalled', 3: 'updates'}.get(idx, 'all')
        self._refresh_list()

    def onSelectionChanged(self, evt):
        self._updateButtons()

    def _get_selected_tag(self) -> str | None:
        sel = self.listCtrl.GetFirstSelected()
        if sel == -1:
            return None
        try:
            return self._rows[sel]
        except Exception:
            return None

    def _find_item_by_tag(self, tag: str):
        for rec in self._items:
            if rec.get('tag') == tag:
                return rec
        return None

    def _updateButtons(self):
        tag = self._get_selected_tag()
        if not tag:
            self.installBtn.Enable(False)
            self.updateBtn.Enable(False)
            self.deleteBtn.Enable(False)
            return
        rec = self._find_item_by_tag(tag)
        installed = rec.get('installed', False) if rec else False
        statusKey = rec.get('status') if rec else None
        self.installBtn.Enable(not installed)
        self.deleteBtn.Enable(installed)
        self.updateBtn.Enable(installed and statusKey == 'updateAvailable')

    def onRefresh(self, evt):
        self.populate()

    def onInstall(self, evt):
        tag = self._get_selected_tag()
        if not tag:
            ui.message(_("No dictionary selected"))
            return
        # Reuse the downloader dialog flow
        def _after():
            wx.CallAfter(self.populate)
        LanguageDictionaryDownloader(tag, ask_user=False, on_finished=_after).download()

    def onDelete(self, evt):
        sel = self.listCtrl.GetFirstSelected()
        if sel == -1:
            ui.message(_("No dictionary selected"))
            return
        try:
            tag = self._rows[sel]
        except Exception:
            ui.message(_("No dictionary selected"))
            return
        confirm = gui.messageBox(
            # Translators: confirmation to delete a downloaded dictionary
            _("Remove dictionary files for {tag}?").format(tag=tag),
            _("Confirm deletion"),
            style=wx.YES | wx.NO | wx.ICON_WARNING,
            parent=self,
        )
        if confirm != wx.YES:
            return
        if remove_installed_dictionary(tag):
            ui.message(_("Dictionary removed"))
        else:
            ui.message(_("Nothing removed"))
        self.populate()

    def onUpdate(self, evt):
        tag = self._get_selected_tag()
        if not tag:
            ui.message(_("No dictionary selected"))
            return
        # Check if downloadable and remote newer
        rec = self._find_item_by_tag(tag)
        if not rec or rec.get("status") != "updateAvailable":
            ui.message(_("No update available"))
            return
        # Reuse the downloader dialog flow
        def _after():
            wx.CallAfter(ui.message, _("Dictionary updated"))
            wx.CallAfter(self.populate)
        LanguageDictionaryDownloader(tag, ask_user=False, on_finished=_after).download()


class LanguageDictionaryDownloader:
    def __init__(self, language_tag, ask_user=True, on_finished=None):
        self.language_tag = language_tag
        self.ask_user = ask_user
        self.on_finished = on_finished
        self.language_description = languageHandler.getLanguageDescription(language_tag)
        self.progress_dialog = None
        self._overall_progress = 0

    def update_progress(self, progress):
        """Handle both overall (int) and per-file (dict) progress payloads."""
        if isinstance(progress, dict):
            file = progress.get("file")
            pct = int(progress.get("progress", 0))
            # Translators: progress message showing per-file percentage and overall.
            msg = _("Downloading {file}: {pct}% (Total: {total}%)").format(
                file=file, pct=pct, total=self._overall_progress
            )
            try:
                self.progress_dialog.Update(self._overall_progress, msg)
            except Exception:
                pass
            return
        try:
            self._overall_progress = int(progress)
        except Exception:
            self._overall_progress = 0
        # Translators: message of a progress dialog
        msg = _("Downloaded: {progress}%").format(progress=self._overall_progress)
        try:
            self.progress_dialog.Update(self._overall_progress, msg)
        except Exception:
            pass

    def done_callback(self, exception):
        self.progress_dialog.Hide()
        self.progress_dialog.Destroy()
        del self.progress_dialog
        if exception is None:
            wx.CallAfter(
                gui.messageBox,
                _("Successfully downloaded dictionary for  language {lang}").format(
                    lang=self.language_description
                ),
                _("Dictionary Downloaded"),
                style=wx.ICON_INFORMATION,
            )
        else:
            wx.CallAfter(
                gui.messageBox,
                _(
                    "Cannot download dictionary for language {lang}.\nPlease check your connection and try again."
                ).format(lang=self.language_description),
                _("Download Failed"),
                style=wx.ICON_ERROR,
            )
            log.exception(
                f"Failed to download language dictionary.\nException: {exception}"
            )
        # After UI is closed, invoke external completion callback if provided
        if self.on_finished:
            try:
                self.on_finished()
            except Exception:
                pass

    def download(self):
        if self.ask_user:
            retval = gui.messageBox(
                _(
                    "Dictionary for language {lang} is missing.\nWould you like to download it?"
                ).format(lang=self.language_description),
                _("Download Language Dictionary"),
                style=wx.YES | wx.NO | wx.ICON_ASTERISK,
                parent=gui.mainFrame,
            )
            if retval == wx.NO:
                return
        self.progress_dialog = wx.ProgressDialog(
            # Translators: title of a progress dialog
            title=_("Downloading Dictionary For Language {lang}").format(
                lang=self.language_description
            ),
            # Translators: message of a progress dialog
            message=_("Retrieving download information..."),
            parent=gui.mainFrame,
        )
        self.progress_dialog.CenterOnScreen()
        download_language_dictionary(
            self.language_tag, self.update_progress, self.done_callback
        )
