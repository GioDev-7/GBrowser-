import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtGui import *

APP_NAME = "GBrowser"
ORG_NAME = "GioDev-7"
HOMEPAGE = "https://search.brave.com/"

# ---------- AdBlock ----------
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.enabled = True
        self.blocked_domains = [
            "doubleclick.net", "ads.google", "googlesyndication.com",
            "adservice.google", "facebook.net", "analytics"
        ]

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl().toString().lower()
        if any(d in url for d in self.blocked_domains):
            info.block(True)

# ---------- Browser Tab ----------
class Browser(QWebEngineView):
    def __init__(self, user_agent=""):
        super().__init__()
        self.profile = QWebEngineProfile()  # profilo separato
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.page_ = QWebEnginePage(self.profile, self)
        self.setPage(self.page_)

        # User agent personalizzato
        if user_agent:
            self.profile.setHttpUserAgent(user_agent)

        # Protezione fingerprinting
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)

        # Mascheramento Canvas / WebGL
        self.page_.runJavaScript("""
            HTMLCanvasElement.prototype.getContext = function() { return null; };
            WebGLRenderingContext.prototype.getParameter = function() { return null; };
            document.fonts = undefined;
        """)

        self.setUrl(QUrl(HOMEPAGE))

# ---------- Main Window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(True)
        self.addToolBar(self.toolbar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # User agent
        self.current_user_agent = ""

        # AdBlock
        self.adblock = AdBlocker()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.adblock)

        # Pulsanti emoji
        self.add_btn("⬅️", self.browser_back)
        self.add_btn("➡️", self.browser_forward)
        self.add_btn("🔄", self.browser_reload)
        self.add_btn("🏠", self.navigate_home)
        self.add_btn("➕", self.add_new_tab)

        # User Agent Combo
        self.user_agent_combo = QComboBox()
        self.user_agent_combo.addItems([
            "Default",
            "Windows Chrome",
            "Mac Safari",
            "Linux Firefox",
            "Mobile Android",
            "Mobile iOS"
        ])
        self.user_agent_combo.currentIndexChanged.connect(self.change_user_agent)
        self.toolbar.addWidget(self.user_agent_combo)

        # URL Bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.urlbar)

        # AdBlock toggle
        self.adblock_btn = QAction("🛡️", self)
        self.adblock_btn.setCheckable(True)
        self.adblock_btn.setChecked(True)
        self.adblock_btn.triggered.connect(self.toggle_adblock)
        self.toolbar.addAction(self.adblock_btn)

        # Tema scuro
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QToolBar { background-color: #1e1e1e; spacing: 6px; }
            QLineEdit {
                background-color: #2e2e2e;
                color: white;
                border-radius: 6px;
                padding: 4px;
            }
            QTabBar::tab { background: #2e2e2e; color: white; padding: 6px; }
            QTabBar::tab:selected { background: #3e3e3e; }
        """)

        # Prima tab
        self.add_new_tab()

    def add_btn(self, emoji, slot):
        btn = QAction(emoji, self)
        btn.triggered.connect(slot)
        self.toolbar.addAction(btn)

    # ---------- Tabs ----------
    def add_new_tab(self):
        browser = Browser(user_agent=self.current_user_agent)
        i = self.tabs.addTab(browser, "Nuova Tab")
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, b=browser:
                                   self.update_urlbar(qurl, b))
        browser.loadFinished.connect(lambda _, i=i, b=browser:
                                     self.tabs.setTabText(i, b.page().title()))

    def close_tab(self, index):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(index)

    # ---------- Navigazione ----------
    def browser_back(self): self.tabs.currentWidget().back()
    def browser_forward(self): self.tabs.currentWidget().forward()
    def browser_reload(self): self.tabs.currentWidget().reload()
    def navigate_home(self): self.tabs.currentWidget().setUrl(QUrl(HOMEPAGE))
    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("https")
        self.tabs.currentWidget().setUrl(q)
    def update_urlbar(self, q, browser=None):
        if browser != self.tabs.currentWidget():
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    # ---------- User Agent ----------
    def change_user_agent(self):
        ua_map = {
            "Default": "",
            "Windows Chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mac Safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Linux Firefox": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mobile Android": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mobile iOS": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
        }
        selected = self.user_agent_combo.currentText()
        self.current_user_agent = ua_map.get(selected, "")
        # Applica a tutte le tab esistenti
        for i in range(self.tabs.count()):
            b = self.tabs.widget(i)
            b.profile.setHttpUserAgent(self.current_user_agent)
            b.reload()

    # ---------- AdBlock ----------
    def toggle_adblock(self):
        self.adblock.enabled = self.adblock_btn.isChecked()

# ---------- App bootstrap ----------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# Copyright (C) 2025 GioDev-7
#
# This file is part of [GBrowser].
#
# [GBrowser] is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# --- Etica d’uso ---
# Ti invito a usare questo software in modo etico e responsabile.
# Non utilizzarlo per scopi dannosi, discriminatori, fraudolenti o che violino i diritti di altri.
# La libertà che ti viene concessa porta con sé anche la responsabilità di rispettare gli altri.
#
# Nota: Sebbene questo software sia distribuito sotto licenza GNU GPL v3,
# è consigliabile contattare GioDev-7 prima di redistribuirlo o modificarlo pubblicamente.
# Questo aiuta a mantenere coerenza, rispetto e collaborazione tra sviluppatori.
