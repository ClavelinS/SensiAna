from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QToolButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from view.utils.style_sheet import StyleSheets

class CollapsableBox(QGroupBox):
    def __init__(self, title: str="", icon_expand_path: str="view/img/expand.png", icon_collapse_path: str="view/img/collapse.png", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.icon_expand = QIcon(icon_expand_path)
        self.icon_collapse = QIcon(icon_collapse_path)

        self.setStyleSheet(StyleSheets().group_style_sheet)

        layout = QVBoxLayout(self)

        # Contenu masqué au départ
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_widget.setVisible(False)

        # Bouton avec icône
        self.toggle_button = QToolButton()
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setIcon(self.icon_expand)
        if self.title_text != "":
            self.toggle_button.setText(self.title_text)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet(StyleSheets().toggle_button)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_content)

        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_widget)

    def toggle_content(self):
        is_visible = self.content_widget.isVisible()
        self.content_widget.setVisible(not is_visible)

        # Met à jour l’icône
        if is_visible:
            self.toggle_button.setIcon(self.icon_expand)
        else:
            self.toggle_button.setIcon(self.icon_collapse)

    def addWidget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def setContentWidget(self, widget: QWidget):
        # Efface le contenu précédent si nécessaire
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self.content_layout.addWidget(widget)

    def _on_toggle(self, checked, action=None):
        self.toggled.emit(checked)
        if action:
            action()