from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from view.utils.style_sheet import StyleSheets

class CustomLineEdit(QWidget):
    def __init__(self, label_text:str="Label", initial_value:str="", tooltip:str="", parent=None):
            super().__init__(parent)

            stylesheets = StyleSheets()

            self._label = QLabel(label_text)
            self._label.setFont(QFont("Arial", 9, QFont.Bold))
            self._label.setStyleSheet(stylesheets.label_customLineEdit)

            self._input = QLineEdit()
            self._input.setText(initial_value)
            self._input.setStyleSheet(stylesheets.qlineedit_customLineEdit)
            if tooltip != "":
                self._input.setToolTip(tooltip)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self._label, alignment=Qt.AlignLeft)
            layout.addWidget(self._input)

            self.label_offset = 25
            # Ajustement position du label : on le déplace légèrement vers le haut pour chevaucher la bordure
            self._label.move(10, self.label_offset-self._label.height() // 2)  # horizontal décallage pour coller au padding left
            self._label.raise_()

            self.setFixedHeight(60)


    def text(self) -> str:
        return self._input.text()
    
    def setTooltip(self, tooltip:str) -> None:
        self._input.setToolTip(tooltip)

        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # On force la position du label pour chevaucher bordure en haut à gauche
        self._label.move(10, self.label_offset-self._label.height() // 2)

    def setText(self, text_to_set:str) -> None:
        self._input.setText(text_to_set)

        return None

# class CustomLineEdit(QWidget):
#     def __init__(self, label_text="Label", initial_value="", parent=None):
#         super().__init__(parent)

#         stylesheets = StyleSheets()

#         # QLineEdit principal
#         self._input = QLineEdit(self)
#         self._input.setText(initial_value)
#         self._input.setStyleSheet(stylesheets.qlineedit)
#         self._input.setContentsMargins(0, 20, 0, 0)  # laisser de l'espace pour le label

#         # Label flottant
#         self._label = QLabel(label_text, self)
#         self._label.setStyleSheet(stylesheets.label)
#         self._label.setFont(QFont("Arial", 9, QFont.Bold))
#         self.label_offset = 5
#         self._label.move(5, self.label_offset)
#         self._label.raise_()

#         # Layout principal
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self._input)

#         # Ajuster la hauteur pour que le label ne soit pas coupé
#         self.setFixedHeight(self._input.sizeHint().height() + self.label_offset)

#     def text(self) -> str:
#         return self._input.text()

#     def setText(self, text_to_set: str) -> None:
#         self._input.setText(text_to_set)

#     def setTooltip(self, tooltip: str) -> None:
#         self._input.setToolTip(tooltip)

#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         # Repositionner le label pour chevaucher correctement la bordure
#         self._label.move(5, self.label_offset)

