import sys
import psutil

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
)


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("linux-control-center")
window.resize(800, 500)

window.setStyleSheet("""
    QWidget {
        background-color: #101319;
        color: #e8eaf0;
        font-family: sans-serif;
     }
     QLabel#title {
         font-size: 28px;
         font-weight: bold;
     }
     QLabel#info {
         font-size: 16px;
         color: #82aaff;
     }
""")

layout = QVBoxLayout(window)

title = QLabel("linux-control-center")
title.setObjectName("title")

info = QLabel(
    f"CPU: {psutil.cpu_count()} logical processors\n"
    f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB\n"
    f"Platform: {sys.platform}"
)
info.setObjectName("info")

layout.addWidget(title)
layout.addWidget(info)
layout.addStretch()

window.show()
sys.exit(app.exec())