"""Tema carbón: superficies oscuras y estados diferenciados por forma y contraste."""
from PySide6.QtGui import QColor, QPalette

BG = "#0c0d0f"
PANEL = "#121315"
LINE = "#2b2d32"
INK = "#e8e9ec"
MUTED = "#b5bbc5"
# Los nombres se conservan para no acoplar el algoritmo a la presentación.
CYAN = "#86efac"
GOLD = "#d9f99d"
VIOLET = "#a8b5ad"
GREEN = "#4ade80"

def aplicar_paleta(app):
    paleta = QPalette()
    for rol, tinta in [(QPalette.ColorRole.Window,BG), (QPalette.ColorRole.WindowText,INK),
                       (QPalette.ColorRole.Base,PANEL), (QPalette.ColorRole.AlternateBase,"#191b1e"),
                       (QPalette.ColorRole.Text,INK), (QPalette.ColorRole.Button,"#24262b"),
                       (QPalette.ColorRole.ButtonText,INK), (QPalette.ColorRole.Highlight,"#24543a"),
                       (QPalette.ColorRole.HighlightedText,INK), (QPalette.ColorRole.ToolTipBase,"#24262b"),
                       (QPalette.ColorRole.ToolTipText,INK)]:
        paleta.setColor(rol,QColor(tinta))
    app.setPalette(paleta)

STYLE = f"""
QMainWindow, QDialog {{ background: {BG}; }}
QWidget {{ color: {INK}; font-family: 'Segoe UI'; font-size: 13px; }}
QLabel {{ background: transparent; }}
QFrame#cabecera {{ background: {BG}; border-bottom: 1px solid {LINE}; }}
QFrame#rail {{ background: #101113; border-right: 1px solid {LINE}; }}
QFrame#espacioGrafo {{ background: {PANEL}; border: 1px solid #25272c; border-radius: 12px; }}
QFrame#detalle, QFrame#metadatos, QFrame#transporte {{ background: {BG}; border: none; }}
QFrame#card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 8px; }}
QLabel#eyebrow {{ color: {MUTED}; font-size: 10px; font-weight: 600; }}
QPushButton {{ background: #1e2024; border: 1px solid #35383e; border-radius: 7px; padding: 8px 12px; font-size: 12px; }}
QPushButton:hover {{ background: #2b2e34; border-color: #86efac; }}
QPushButton:pressed {{ background: #151619; }}
QPushButton:disabled {{ color: #62656d; background: #141518; border-color: #292b30; }}
QPushButton#primary {{ background: #24543a; border: 1px solid #4ade80; font-weight: 600; }}
QPushButton#primary:hover {{ background: #306b49; }}
QPushButton#quiet {{ background: transparent; color: {MUTED}; border: none; }}
QPushButton#quiet:hover {{ background: #222429; color: {INK}; }}
QPushButton#review {{ background: #1c1e22; color: #b1b4bc; border: none; padding: 5px 9px; }}
QComboBox, QDoubleSpinBox {{ background: #1a1c20; color: {INK}; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{ background: #1a1c20; color: {INK}; selection-background-color: #24543a; }}
QCheckBox {{ color: {MUTED}; spacing: 7px; font-size: 11px; }}
QCheckBox::indicator {{ width: 12px; height: 12px; border: 1px solid #5b5e67; border-radius: 3px; background: #16171a; }}
QCheckBox::indicator:checked {{ background: #4ade80; border: 3px solid #24543a; }}
QSlider::groove:horizontal {{ background: #303239; height: 3px; border-radius: 1px; }}
QSlider::sub-page:horizontal {{ background: #4ade80; }}
QSlider::handle:horizontal {{ background: #bbf7d0; width: 10px; height: 10px; margin: -4px 0; border-radius: 5px; }}
QSplitter::handle {{ background: #1f2126; }}
QSplitter::handle:hover {{ background: #43464f; }}
QTabWidget::pane {{ background: {PANEL}; border: 1px solid {LINE}; }}
QTabBar::tab {{ color: {MUTED}; padding: 9px 13px; font-size: 11px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {INK}; border-bottom: 2px solid #4ade80; }}
QTableWidget, QListWidget {{ background: {PANEL}; alternate-background-color: #191b1f; color: {INK}; border: none; outline: none; }}
QTableWidget::item {{ padding: 4px; }}
QListWidget#secuencia {{ background: transparent; }}
QListWidget#secuencia::item {{ padding: 11px 9px; border-left: 2px solid transparent; border-bottom: 1px solid #222429; color: #b5bbc5; font-size: 12px; }}
QListWidget#secuencia::item:selected {{ background: #193c2a; border-left: 2px solid #4ade80; color: #eff0f2; }}
QListWidget#secuencia::item:hover {{ background: #1c1e22; color: #c5c9d0; }}
QTableWidget::item:selected {{ background: #24543a; color: {INK}; }}
QHeaderView::section {{ background: #1e2025; color: {MUTED}; padding: 7px 4px; border: none; font-size: 10px; }}
QTableCornerButton::section {{ background: #1e2025; border: none; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: #16171a; width: 6px; }}
QScrollBar::handle:vertical {{ background: #474b54; min-height: 28px; border-radius: 3px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: #16171a; height: 6px; }}
QScrollBar::handle:horizontal {{ background: #474b54; min-width: 28px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QMenu, QToolTip {{ background: #202227; color: {INK}; border: 1px solid #3c3f47; padding: 6px; }}
QMenu::item {{ padding: 8px 18px; }}
QMenu::item:selected {{ background: #24543a; }}
"""
