"""浅色/深色主题：颜色令牌 + 全局样式表。"""
from __future__ import annotations

import sys

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette

LIGHT = {
    "chrome": "#E8EAEE",     # 标签栏（Windows 11 上标题栏也用这个颜色，连成一片）
    "bg": "#F4F5F7",
    "surface": "#FFFFFF",
    "surface2": "#F0F1F4",
    "hover": "rgba(20, 30, 50, 0.06)",
    "pressed": "rgba(20, 30, 50, 0.10)",
    "border": "#E2E4E9",
    "border_strong": "#CDD1D8",
    "text": "#1F2329",
    "text2": "#5B6270",
    "text3": "#9096A1",
    "accent": "#3D6DF2",
    "accent_hover": "#2F5CE0",
    "accent_soft": "rgba(61, 109, 242, 0.12)",
    "accent_soft2": "rgba(61, 109, 242, 0.20)",
    "accent_text": "#FFFFFF",
    "canvas": "#E6E8EC",
    "page_shadow": "rgba(15, 23, 42, 0.10)",
    "danger": "#E5484D",
    "success": "#2BA471",
    "warning": "#E89B0C",
    "selection": "rgba(61, 109, 242, 0.28)",
    "search_hit": "rgba(255, 196, 0, 0.40)",
    "search_current": "rgba(255, 128, 0, 0.55)",
    "read_hl": "rgba(61, 109, 242, 0.18)",
    "tooltip_bg": "#1F2329",
    "tooltip_text": "#FFFFFF",
}

DARK = {
    "chrome": "#121315",
    "bg": "#1B1C1F",
    "surface": "#25262B",
    "surface2": "#2D2F35",
    "hover": "rgba(255, 255, 255, 0.07)",
    "pressed": "rgba(255, 255, 255, 0.12)",
    "border": "#34363D",
    "border_strong": "#464953",
    "text": "#E7E8EA",
    "text2": "#A8ADB6",
    "text3": "#737882",
    "accent": "#5B8CFF",
    "accent_hover": "#7AA2FF",
    "accent_soft": "rgba(91, 140, 255, 0.18)",
    "accent_soft2": "rgba(91, 140, 255, 0.28)",
    "accent_text": "#FFFFFF",
    "canvas": "#131416",
    "page_shadow": "rgba(0, 0, 0, 0.45)",
    "danger": "#F2555A",
    "success": "#3DBE8B",
    "warning": "#F0AD2B",
    "selection": "rgba(91, 140, 255, 0.35)",
    "search_hit": "rgba(255, 196, 0, 0.40)",
    "search_current": "rgba(255, 128, 0, 0.60)",
    "read_hl": "rgba(91, 140, 255, 0.24)",
    "tooltip_bg": "#E7E8EA",
    "tooltip_text": "#1B1C1F",
}

# 界面字体。Windows 上把微软雅黑 UI 放在最前：它的西文就是 Segoe UI 的字形，而行高和基线按中文设计；
# 以前 Segoe UI 在前、中文回退到雅黑时，行高按 Segoe UI 算，中文字偏下、看起来像被裁掉了一点
if sys.platform == "win32":
    FONT_FAMILIES = ["Microsoft YaHei UI", "Segoe UI", "Microsoft YaHei"]
elif sys.platform == "darwin":
    FONT_FAMILIES = [".AppleSystemUIFont", "PingFang SC", "Helvetica Neue"]
else:
    FONT_FAMILIES = ["Inter", "Noto Sans CJK SC", "WenQuanYi Zen Hei"]


class ThemeManager(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.mode = "system"     # system / light / dark
        self.colors = dict(LIGHT)
        self.dark = False
        self._styled = False

    def c(self, key: str) -> str:
        return self.colors[key]

    def qc(self, key: str) -> QColor:
        return parse_color(self.colors[key])

    def system_is_dark(self) -> bool:
        hints = QGuiApplication.styleHints()
        try:
            return hints.colorScheme() == Qt.ColorScheme.Dark
        except Exception:
            pal = QGuiApplication.palette()
            return pal.color(QPalette.Window).lightness() < 128

    def apply(self, app, mode: str | None = None):
        if mode:
            self.mode = mode
        if not self._styled:
            self._styled = True
            app.setStyle("Fusion")  # 各平台外观一致，且与样式表配合最好
            font = QFont(app.font())
            font.setFamilies(FONT_FAMILIES)
            if sys.platform == "win32":
                # 缩放 125%、150% 时默认不做字形微调，中文的横笔画会糊成两个像素；按像素对齐后清楚得多
                font.setHintingPreference(QFont.PreferFullHinting)
            app.setFont(font)
            if sys.platform == "win32":
                self._title_filter = TitleBarFilter(self)
                app.installEventFilter(self._title_filter)
        self.dark = self.mode == "dark" or (self.mode == "system" and self.system_is_dark())
        self.colors = dict(DARK if self.dark else LIGHT)
        from .icons import themed_file

        css_vars = dict(self.colors)
        css_vars["_check"] = themed_file("check", "#FFFFFF")
        css_vars["_chevron"] = themed_file("chevron-down", self.colors["text2"])
        app.setStyleSheet(stylesheet(css_vars))
        pal = app.palette()
        c = self.colors
        pal.setColor(QPalette.Window, parse_color(c["bg"]))
        pal.setColor(QPalette.Base, parse_color(c["surface"]))
        pal.setColor(QPalette.AlternateBase, parse_color(c["surface2"]))
        pal.setColor(QPalette.Text, parse_color(c["text"]))
        pal.setColor(QPalette.WindowText, parse_color(c["text"]))
        pal.setColor(QPalette.ButtonText, parse_color(c["text"]))
        pal.setColor(QPalette.Button, parse_color(c["surface"]))
        pal.setColor(QPalette.Highlight, parse_color(c["accent"]))
        pal.setColor(QPalette.HighlightedText, parse_color(c["accent_text"]))
        pal.setColor(QPalette.PlaceholderText, parse_color(c["text3"]))
        pal.setColor(QPalette.ToolTipBase, parse_color(c["tooltip_bg"]))
        pal.setColor(QPalette.ToolTipText, parse_color(c["tooltip_text"]))
        app.setPalette(pal)
        if sys.platform == "win32":
            for w in app.topLevelWidgets():
                if w.isVisible() and w.windowType() in (Qt.Window, Qt.Dialog):
                    self.style_title_bar(w)
        self.changed.emit()

    def style_title_bar(self, w):
        """Windows：标题栏颜色跟随主题。窗口可以用 titleColor 属性指定底色（颜色令牌名），默认用 bg。"""
        from .platform_win import style_title_bar

        key = w.property("titleColor") or "bg"
        style_title_bar(int(w.winId()), self.qc(key if key in self.colors else "bg"), self.qc("text"), self.dark)


class TitleBarFilter(QObject):
    """Windows：窗口显示时给标题栏上色；菜单和提示框改成透明底，去掉系统加的直角阴影。"""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Polish and obj.isWidgetType() and _is_popup(obj):
            make_popup_rounded(obj)
        elif (event.type() == QEvent.Show and obj.isWidgetType() and obj.isWindow()
                and obj.windowType() in (Qt.Window, Qt.Dialog)):  # 不管菜单、提示等弹出窗口
            theme.style_title_bar(obj)
        return False


def _is_popup(w) -> bool:
    return w.inherits("QMenu") or w.inherits("QTipLabel")


def make_popup_rounded(w):
    """菜单、提示框的圆角来自样式表，但 Windows 上弹出窗口是不透明的矩形，圆角外面露出底色，
    系统还会在右边和下边画一道直角阴影（看起来像菜单底下多了一条黑线）。
    改成透明底、不要系统阴影，就只剩样式表画的圆角和边框。必须在窗口真正创建之前设置：
    QMenu 和 QTipLabel 都会在显示之前先 polish，这时候还没有创建窗口。
    """
    if w.property("_folioRounded") or w.testAttribute(Qt.WA_WState_Created):
        return
    w.setProperty("_folioRounded", True)
    w.setWindowFlags(w.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    w.setAttribute(Qt.WA_TranslucentBackground)


def parse_color(s: str) -> QColor:
    s = s.strip()
    if s.startswith("rgba"):
        r, g, b, a = [float(x) for x in s[s.index("(") + 1:s.index(")")].split(",")]
        return QColor(int(r), int(g), int(b), int(a * 255))
    return QColor(s)


theme = ThemeManager()


def stylesheet(c: dict) -> str:
    return f"""
* {{
    font-size: 13px;
    color: {c['text']};
    outline: none;
}}
QMainWindow, QDialog, #Root {{ background: {c['bg']}; }}
QWidget#Surface, QFrame#Surface {{ background: {c['surface']}; }}
QFrame#Card {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QFrame#InfoBar {{
    background: {c['accent_soft']};
    border: none;
    border-bottom: 1px solid {c['border']};
}}
QFrame#Hairline {{ background: {c['border']}; max-height: 1px; min-height: 1px; border: none; }}
QFrame#VHairline {{ background: {c['border']}; max-width: 1px; min-width: 1px; border: none; }}
QLabel {{ background: transparent; }}
QLabel#Muted {{ color: {c['text2']}; }}
QLabel#Faint {{ color: {c['text2']}; font-size: 12px; }}
QLabel#H1 {{ font-size: 26px; font-weight: 600; }}
QLabel#H2 {{ font-size: 17px; font-weight: 600; }}
QLabel#H3 {{ font-size: 14px; font-weight: 600; }}
QLabel#SectionTitle {{ color: {c['text2']}; font-size: 12px; font-weight: 600; }}
QLabel#PageTitle {{ font-size: 22px; font-weight: 600; }}
QLabel#RowTitle {{ font-size: 13px; }}

/* ---------- 顶部栏 ---------- */
#TopBar {{ background: {c['surface']}; border-bottom: 1px solid {c['border']}; }}
#OptionsBar {{ background: {c['surface']}; border-bottom: 1px solid {c['border']}; }}
#TabStrip {{ background: {c['chrome']}; }}

QToolButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 5px;
}}
QToolButton:hover {{ background: {c['hover']}; }}
QToolButton:pressed {{ background: {c['pressed']}; }}
QToolButton:checked {{ background: {c['accent_soft']}; }}
QToolButton:disabled {{ background: transparent; }}
/* Qt 会在带文字的工具按钮右边多留 8px，这里扣掉，左右才对称 */
QToolButton[textButton="true"] {{ padding: 5px 3px 5px 10px; color: {c['text']}; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}

QPushButton {{
    background: {c['surface']};
    border: 1px solid {c['border_strong']};
    border-radius: 8px;
    padding: 7px 16px;
    min-height: 18px;
}}
QPushButton:hover {{ background: {c['surface2']}; }}
QPushButton:pressed {{ background: {c['pressed']}; }}
QPushButton:disabled {{ color: {c['text3']}; border-color: {c['border']}; }}
QPushButton[primary="true"] {{
    background: {c['accent']};
    border: 1px solid {c['accent']};
    color: {c['accent_text']};
    font-weight: 600;
}}
QPushButton[primary="true"]:hover {{ background: {c['accent_hover']}; border-color: {c['accent_hover']}; }}
QPushButton[primary="true"]:disabled {{ background: {c['border_strong']}; border-color: {c['border_strong']}; color: {c['surface']}; }}
QPushButton[flat="true"] {{ background: transparent; border: none; color: {c['accent']}; padding: 6px 8px; }}
QPushButton[flat="true"]:hover {{ background: {c['accent_soft']}; }}

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c['surface']};
    border: 1px solid {c['border_strong']};
    border-radius: 8px;
    padding: 5px 9px;
    selection-background-color: {c['accent']};
    selection-color: {c['accent_text']};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {c['accent']};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {c['text3']}; background: {c['surface2']}; border-color: {c['border']};
}}
QLineEdit#Compact {{ padding: 3px 6px; border-radius: 6px; }}
QLineEdit#Search {{ padding-left: 8px; border-radius: 8px; background: {c['surface2']}; border: 1px solid transparent; }}
QLineEdit#Search:focus {{ background: {c['surface']}; border: 1px solid {c['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0; border: none; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ image: url({c['_chevron']}); width: 12px; height: 12px; margin-right: 6px; }}
QComboBox QAbstractItemView {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {c['accent_soft']};
    selection-color: {c['text']};
}}

QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px; height: 16px;
    border: 1.5px solid {c['border_strong']};
    background: {c['surface']};
}}
QCheckBox::indicator {{ border-radius: 4px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; image: url({c['_check']}); }}
QRadioButton::indicator:checked {{ border: 5px solid {c['accent']}; background: {c['surface']}; }}

QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {c['surface']}; border: 2px solid {c['accent']};
    width: 12px; height: 12px; margin: -6px 0; border-radius: 8px;
}}

QProgressBar {{
    background: {c['surface2']}; border: none; border-radius: 4px; height: 8px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 4px; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['border_strong']}; border-radius: 4px; min-height: 36px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: {c['text3']}; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {c['border_strong']}; border-radius: 4px; min-width: 36px; margin: 2px 0; }}
QScrollBar::handle:horizontal:hover {{ background: {c['text3']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{
    background: {c['surface']};
    border: 1px solid {c['border_strong']};
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{ padding: 7px 28px 7px 12px; border-radius: 6px; background: transparent; }}
QMenu::item:selected {{ background: {c['hover']}; }}
QMenu::item:disabled {{ color: {c['text3']}; }}
QMenu::icon {{ padding-left: 10px; }}
QMenu::separator {{ height: 1px; background: {c['border']}; margin: 5px 6px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 6px; }}

QToolTip {{
    background: {c['tooltip_bg']}; color: {c['tooltip_text']};
    border: none; border-radius: 6px; padding: 5px 8px; font-size: 12px;
}}

QListWidget, QTreeWidget, QListView, QTreeView, QTableWidget {{
    background: transparent;
    border: none;
}}
QListWidget::item, QTreeWidget::item {{ border-radius: 6px; padding: 5px 6px; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {c['hover']}; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {c['accent_soft']}; color: {c['text']}; }}
QTreeView::branch {{ background: transparent; }}
QHeaderView::section {{ background: transparent; border: none; color: {c['text2']}; padding: 4px; }}

/* ---------- 标签栏：选中的标签和下面的工具栏连在一起，像浏览器一样 ---------- */
QTabBar#DocTabs {{ background: transparent; }}
QTabBar#DocTabs::tab {{
    background: transparent;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    height: 34px;
    padding: 0 0 0 12px;
    margin: 0 2px 0 0;
    color: {c['text2']};
    min-width: 72px;
    max-width: 220px;
}}
QTabBar#DocTabs::tab:hover {{ background: {c['hover']}; color: {c['text']}; }}
QTabBar#DocTabs::tab:selected {{ background: {c['surface']}; color: {c['text']}; }}
QTabBar#DocTabs[home="true"]::tab:selected {{ background: transparent; color: {c['text2']}; }}
QTabBar#DocTabs[home="true"]::tab:selected:hover {{ background: {c['hover']}; color: {c['text']}; }}
QTabBar#DocTabs QToolButton {{ background: {c['chrome']}; border: none; border-radius: 6px; padding: 0; }}
QTabBar#DocTabs QToolButton:hover {{ background: {c['hover']}; }}
QTabBar#DocTabs QToolButton#TabClose {{ background: transparent; border-radius: 5px; padding: 0; }}
QTabBar#DocTabs QToolButton#TabClose:hover {{ background: {c['pressed']}; }}
QTabBar::tear {{ width: 0; border: none; }}
#TabStrip QToolButton {{ border-radius: 7px; }}
QToolButton#HomeTab {{
    border-radius: 0;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}
QToolButton#HomeTab:checked {{ background: {c['bg']}; }}
QToolButton#UpdatePill {{
    background: {c['accent_soft']};
    color: {c['accent']};
    border-radius: 13px;
    padding: 3px 4px 3px 8px;
    font-size: 12px;
    font-weight: 600;
}}
QToolButton#UpdatePill:hover {{ background: {c['accent_soft2']}; }}

QSplitter::handle {{ background: {c['border']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}

#Sidebar {{ background: {c['surface']}; }}
#SidebarHeader {{ background: {c['surface']}; }}

#FloatingBar {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}
#Toast {{
    background: {c['tooltip_bg']};
    border-radius: 10px;
}}
#Toast QLabel {{ color: {c['tooltip_text']}; }}

#DropZone {{
    background: {c['surface']};
    border: 1.5px dashed {c['border_strong']};
    border-radius: 16px;
}}
#DropZone[hover="true"] {{ border-color: {c['accent']}; background: {c['accent_soft']}; }}
#ToolCard {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}
#ToolCard:hover {{ border-color: {c['accent']}; }}
#RecentItem {{ background: transparent; border-radius: 10px; }}
#RecentItem:hover {{ background: {c['hover']}; }}
#Swatch {{ border-radius: 11px; }}
#DialogHeader {{ background: {c['surface']}; border-bottom: 1px solid {c['border']}; }}
#DialogFooter {{ background: {c['surface']}; border-top: 1px solid {c['border']}; }}
#Segmented {{ background: {c['surface2']}; border: 1px solid {c['border']}; border-radius: 9px; }}
#Segmented QToolButton {{
    border: 1px solid transparent; border-radius: 7px; padding: 5px 14px; color: {c['text2']};
}}
#Segmented QToolButton:hover {{ color: {c['text']}; }}
#Segmented QToolButton:checked {{ background: {c['surface']}; border-color: {c['border_strong']}; color: {c['text']}; }}

/* ---------- 设置 ---------- */
QFrame#SettingsCard {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
}}
QFrame#SettingsCard QFrame#Hairline {{ background: {c['border']}; }}
QListWidget#SettingsNav::item {{ padding: 8px 10px; margin: 1px 0; border-radius: 8px; color: {c['text']}; }}
QListWidget#SettingsNav::item:selected {{ background: {c['accent_soft']}; color: {c['accent']}; }}
QScrollArea#PageScroll, QScrollArea#PageScroll > QWidget > QWidget {{ background: transparent; border: none; }}
#SettingsFooter {{ background: {c['bg']}; border-top: 1px solid {c['border']}; }}
"""
