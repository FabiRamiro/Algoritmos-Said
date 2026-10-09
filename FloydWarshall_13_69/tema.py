"""Tema carbón: superficies oscuras y estados diferenciados por forma y contraste."""
from PySide6.QtGui import QColor, QPalette

BG = "#0c0d0f"
PANEL = "#121315"
LINE = "#2b2d32"
INK = "#e8e9ec"
MUTED = "#999ca4"
# Los nombres se conservan para no acoplar el algoritmo a la presentación.
CYAN = "#bec1c8"
GOLD = "#f0f1f3"
VIOLET = "#969aa4"
GREEN = "#d6d9df"

def aplicar_paleta(app):
    paleta = QPalette()
    for rol, tinta in [(QPalette.ColorRole.Window,BG), (QPalette.ColorRole.WindowText,INK),
                       (QPalette.ColorRole.Base,PANEL), (QPalette.ColorRole.AlternateBase,"#191b1e"),
                       (QPalette.ColorRole.Text,INK), (QPalette.ColorRole.Button,"#24262b"),
                       (QPalette.ColorRole.ButtonText,INK), (QPalette.ColorRole.Highlight,"#363940"),
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
QPushButton:hover {{ background: #2b2e34; border-color: #626670; }}
QPushButton:pressed {{ background: #151619; }}
QPushButton:disabled {{ color: #62656d; background: #141518; border-color: #292b30; }}
QPushButton#primary {{ background: #34373e; border: 1px solid #747883; font-weight: 600; }}
QPushButton#primary:hover {{ background: #454951; }}
QPushButton#quiet {{ background: transparent; color: {MUTED}; border: none; }}
QPushButton#quiet:hover {{ background: #222429; color: {INK}; }}
QPushButton#review {{ background: #1c1e22; color: #b1b4bc; border: none; padding: 5px 9px; }}
QComboBox, QDoubleSpinBox {{ background: #1a1c20; color: {INK}; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{ background: #1a1c20; color: {INK}; selection-background-color: #34373e; }}
QCheckBox {{ color: {MUTED}; spacing: 7px; font-size: 11px; }}
QCheckBox::indicator {{ width: 12px; height: 12px; border: 1px solid #5b5e67; border-radius: 3px; background: #16171a; }}
QCheckBox::indicator:checked {{ background: #858993; border: 3px solid #34373e; }}
QSlider::groove:horizontal {{ background: #303239; height: 3px; border-radius: 1px; }}
QSlider::sub-page:horizontal {{ background: #989da7; }}
QSlider::handle:horizontal {{ background: #c5c8cf; width: 10px; height: 10px; margin: -4px 0; border-radius: 5px; }}
QSplitter::handle {{ background: #1f2126; }}
QSplitter::handle:hover {{ background: #43464f; }}
QTabWidget::pane {{ background: {PANEL}; border: 1px solid {LINE}; }}
QTabBar::tab {{ color: {MUTED}; padding: 9px 13px; font-size: 11px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {INK}; border-bottom: 2px solid #a6abb5; }}
QTableWidget, QListWidget {{ background: {PANEL}; alternate-background-color: #191b1f; color: {INK}; border: none; outline: none; }}
QTableWidget::item {{ padding: 4px; }}
QListWidget#secuencia {{ background: transparent; }}
QListWidget#secuencia::item {{ padding: 11px 9px; border-left: 2px solid transparent; border-bottom: 1px solid #222429; color: #93979f; font-size: 12px; }}
QListWidget#secuencia::item:selected {{ background: #25282e; border-left: 2px solid #c6cad2; color: #eff0f2; }}
QListWidget#secuencia::item:hover {{ background: #1c1e22; color: #c5c9d0; }}
QTableWidget::item:selected {{ background: #363a43; color: {INK}; }}
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
QMenu::item:selected {{ background: #34373e; }}
"""
