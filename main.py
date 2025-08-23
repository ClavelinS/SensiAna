import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from presenter import MainPresenter

def main():
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Ton Application")
    status_bar = QStatusBar()
    main_window.setStatusBar(status_bar)
    status_bar.showMessage("SensiAna -- V2.2.0")

    # Instancie le presenter en lui passant la fenêtre principale
    presenter = MainPresenter(main_window)

    # Affiche la fenêtre principale
    main_window.show()

    # Démarre la boucle événementielle Qt
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
