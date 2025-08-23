from dataclasses import dataclass

@dataclass 
class StyleSheets:
    _table_style_sheet = ("""
        QTableWidget {
            font-family: Consolas, monospace;
            font-size: 11pt;
            border: 1px solid #cccccc;
            gridline-color: #e0e0e0;
            selection-background-color: #f2d6da; /* sélection rosée */
        }
        QHeaderView::section {
            background-color: #f9f9f9;
            padding: 4px;
            border: 1px solid #dcdcdc;
            font-weight: bold;
            color: #7b1e2b;
        }
        QTableWidget::item {
            padding: 4px;
        }
    """)

    _group_style_sheet = ("""
        QGroupBox {
            border: 1px solid #cccccc;
            border-radius: 6px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            font-weight: bold;
            color: #7b1e2b;
        }
    """)

    _toggle_button = ("""
            QToolButton {
        border: none;
        background: transparent;
        text-align: left;
        padding: 4px;
        font-weight: bold;
        color: #000000; /* reste noir */
    }
    QToolButton:hover {
        background-color: rgba(123, 30, 43, 0.1); /* léger voile bordeaux */
    }
    QToolButton:checked {
        background: transparent;
        color: #000000; /* même en "ouvert", reste noir */
    }

        """)

    _tab = ("""
        /* Contour principal */
        QTabWidget::pane {
            border: none;
            background: #ffffff;
        }

        /* Onglets verticaux (west) */
        QTabBar::tab {
            background: #ffffff;
            color: #444444;
            padding: 2px 6px;     /* encore plus fin */
            margin: 1px 0;
            border-radius: 3px;
            font-weight: 500;
            min-width: 16px;
            min-height: 16px;
            text-align: left;
        }

        /* Onglet sélectionné */
        QTabBar::tab:selected {
            background: #7b1e2b; 
            color: #ffffff;
            font-weight: 700;
            border-left: 3px solid #ffffff; 
            padding-left: 6px;
        }

        /* Onglet au survol */
        QTabBar::tab:hover {
            background: #f9f0f1;
            color: #111111;
        }

        /* Onglets désactivés */
        QTabBar::tab:disabled {
            color: #aaaaaa;
            background: #ffffff;
        }
    """)

    _push_button = ("""
            QPushButton {
                background-color: white;
                color: #7b1e2b;
                border: 1px solid #aaaaaa;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 6px 12px;  /* réduit pour correspondre à QLineEdit */
            }
            QPushButton:hover { background-color: #f8f0f0; }
            QPushButton:pressed { background-color: #f0e0e0; border: 1px solid #7b1e2b;}
        """)

    _dock = ("""
        QFrame {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QPushButton:hover {
            background-color: #f2d6da;
        }
    """) + _push_button

    _combo_box = ("""
        QComboBox {
            background-color: #ffffff;
            color: #333;
            border: 1px solid #7b1e2b;
            border-radius: 4px;
            padding: 3px 6px;
            font-size: 13px;
            min-height: 24px;
        }

        QComboBox:hover {
            background-color: #f9f0f1;
        }

        QComboBox:focus {
            border: 1px solid #7b1e2b;
            background-color: #ffffff;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #7b1e2b;
            background: #ffffff;
        }

        QComboBox::down-arrow {
            image: url(view/img/drop_down_arrow.png);
            width: 10px;
            height: 10px;
        }
    """)

    _slider = ("""
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: #e0e0e0;
            height: 6px;
            border-radius: 3px;
        }

        QSlider::sub-page:horizontal {
            background: #7b1e2b;
            border: 1px solid #777;
            height: 6px;
            border-radius: 3px;
        }

        QSlider::add-page:horizontal {
            background: #d3d3d3;
            border: 1px solid #777;
            height: 6px;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: white;
            border: 1px solid #5c5c5c;
            width: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }

        QSlider::handle:horizontal:hover {
            background: #f0f0f0;
            border: 1px solid #7b1e2b;
        }

        QSlider::groove:vertical {
            border: 1px solid #bbb;
            background: #e0e0e0;
            width: 6px;
            border-radius: 3px;
        }

        QSlider::sub-page:vertical {
            background: #7b1e2b;
            border: 1px solid #777;
            width: 6px;
            border-radius: 3px;
        }

        QSlider::add-page:vertical {
            background: #d3d3d3;
            border: 1px solid #777;
            width: 6px;
            border-radius: 3px;
        }

        QSlider::handle:vertical {
            background: white;
            border: 1px solid #5c5c5c;
            height: 14px;
            margin: 0 -5px;
            border-radius: 7px;
        }

        QSlider::handle:vertical:hover {
            background: #f0f0f0;
            border: 1px solid #7b1e2b;
        }
    """)

    _label_customLineEdit = ("""
        background-color: white;
        color: #999999;
        padding-left: 4px;
        padding-right: 4px;
        padding-top: 1px;
        padding-bottom: 1px;
    """)

    _qlineedit_customLineEdit = ("""
        QLineEdit {
            border: 2px solid #999;
            border-radius: 6px;
            padding: 8px 10px 2px 10px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 2px solid #7b1e2b;
        }
    """)
    
    @property
    def group_style_sheet(self):
        return self._group_style_sheet
    
    @property
    def table_style_sheet(self):
        return self._table_style_sheet
    
    @property
    def toggle_button(self):
        return self._toggle_button
    
    @property
    def tab(self):
        return self._tab
    
    @property
    def push_button(self):
        return self._push_button
    
    @property
    def dock(self):
        return self._dock
    
    @property
    def combo_box(self):
        return self._combo_box
    
    @property
    def slider(self):
        return self._slider
    
    @property
    def label_customLineEdit(self):
        return self._label_customLineEdit
    
    @property
    def qlineedit_customLineEdit(self):
        return self._qlineedit_customLineEdit
