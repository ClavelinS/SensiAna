from PySide6.QtWidgets import QPushButton

from view.utils.style_sheet import StyleSheets

class PushButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheets().push_button)
        self.setFixedHeight(32)
