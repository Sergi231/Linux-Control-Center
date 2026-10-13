import sys
import platform
import time

import psutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# --------------------------------------------------------
# Theme
# --------------------------------------------------------

APP_STYLE = """
QMainWindow, QWidget#central {
    background-color: #101319;
    color: #e8eaf0;
    font-family: "inter", "Segoe UI", "sans-serif";
}

QFrame#sidebar {
    background-color: #151922;
    border-right: 1px solid #252b38;
}

QLabel#brand {
    font-size: 20px;
    font-weight: 700;
    color: #e8eaf0;
}

QLabel#muted {
    color: #8b95a7;
    font-size: 12px;
}

QLabel#page_title {
    font-size: 27px;
    font-weight: 700;
}

QLabel#section_title {
    font-size: 17px;
    font-weight: 600;
}

QLabel#card_title {
    color: #a4aec0;
    font-size: 13px;
    font-weight: 600;
}

QLabel#metric {
    font-size: 34px;
    font-weight: 700;
}

QLabel#body {
    font-size: 13px;
    color: #c1c9d6;
}

QLabel#accent {
    color: #82aaff;
    font-weight: 600;
}

QFrame#card {
    background-color: #181e29;
    border: 1px solid #283142;
    border-radius: 12px;
}

QFrame#info_panel {
    background-color: #181e29;
    border: 1px solid #283142;
    border-radius: 12px;
}

QPushButton#nav_button {
    background-color: transparent;
    color: #a4aec0;
    border: none;
    border-radius: 0px;
    text-align: left;
    padding: 11px 12px;
    font-size: 14px;
}

QPushButton#nav_button:hover {
    background-color: #202736;
    color: #ffffff;
}

QPushButton#nav_button[checked="true"] {
    background-color: #24334c;
    color: #9fc0ff;
    front-weight: 600;
}

QProgressBar {
    background-color: #252d3b;
    border: none;
    border-radius: 4px;
    min-height: 7px;
    max-height: 7px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #82aaff;
    border-radius: 4px;
}

QPushButton#refresh_button {
    background-color: #24334c;
    color: #b9d0ff;
    border: 1px solid #354968;
    border-radius: 8px;
    padding: 9px 14px;
}

QPushButton#refresh_button:hover {
    background-color: #304461;
}

QLabel#status {
    color: #85d6a0;
    font-size: 12px;
}
"""


# --------------------------------------------------------
# Reusable widgets
# --------------------------------------------------------

class MetricCard(QFrame):
    """A card displaying a system metric and progress bar."""
    
    def __init__(self, title, description):
            super().__init__()
            self.setObjectName("card")
            self.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )
            self.setMinimumHeight(190)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 18, 20, 18)
            layout.setSpacing(12)

            self.title_label = QLabel(title.upper())
            self.title_label.setObjectName("card_title")
            
            self.value_label = QLabel("--")
            self.value_label.setObjectName("metric")

            self.description_label = QLabel(description)
            self.description_label.setObjectName("muted")

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)

            layout.addWidget(self.title_label)
            layout.addWidget(self.value_label)
            layout.addWidget(self.description_label)
            layout.addStretch()
            layout.addWidget(self.progress_bar)

    def update_metric(self, value, description):
          value = max(0, min(100, value))
          self.value_label.setText(f"{value:.0f}%")
          self.description_label.setText(description)
          self.progress_bar.setValue(round(value))
          

# ----------------------------------------------
# Main application
# ----------------------------------------------

class LinuxControlCenter(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Linux Control Center")
        self.resize(1100, 720)
        self.setMinimumSize(850, 600)

        self.start_time = time.monotonic()
        self.selected_page = "Overview"

        # Prime the CPU sampler. The first reading may be zero.
        psutil.cpu_percent(interval=None)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self.create_sidebar()
        root.addWidget(sidebar)

        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 26, 30, 22)
        content_layout.setSpacing(22)

        root.addWidget(content, 1)

        # Header
        header = QHBoxLayout()

        heading_box = QVBoxLayout()
        heading_box.setSpacing(5)

        self.page_title = QLabel("System Overview")
        self.page_title.setObjectName("page_title")

        subtitle = QLabel(
             "Monitor your system resources in real-time"
        )
        subtitle.setObjectName("muted")

        heading_box.addWidget(self.page_title)
        heading_box.addWidget(subtitle)

        header.addLayout(heading_box)
        header.addStretch()

        refresh_button = QPushButton("Refresh now")
        refresh_button.setObjectName("refresh_button")
        refresh_button.clicked.connect(self.update_metrics)
        header.addWidget(refresh_button)

        content_layout.addLayout(header)

        # Status
        status_row = QHBoxLayout()

        self.status_label = QLabel("● Monitoring active")
        self.status_label.setObjectName("status")

        status_row.addWidget(self.status_label)
        status_row.addStretch()
        self.last_update_label = QLabel("Last update: --")
        status_row.addWidget(self.last_update_label)

        content_layout.addLayout(status_row)

        # Metrics cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.cpu_card = MetricCard(
             "CPU Usage",
             "Detecting processor..."
        )

        self.ram_card = MetricCard(
             "RAM Usage",
             "Detecting memory..."
        )

        cards_layout.addWidget(self.cpu_card)
        cards_layout.addWidget(self.ram_card)

        content_layout.addLayout(cards_layout)

        # System information
        info_title = QLabel("System Information")
        info_title.setObjectName("section_title")
        content_layout.addWidget(info_title)

        info_panel = QFrame()
        info_panel.setObjectName("info_panel")

        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(15)

        self.platform_value = self.add_info_row(
             info_layout, "Logical processors"
        )    
        self.uptime_value = self.add_info_row(
             info_layout, "Application uptime"
        )
        self.interval_value = self.add_info_row(
             info_layout, "Refresh interval"
        )

        content_layout.addWidget(info_panel)
        content_layout.addStretch()

        footer = QLabel(
             "Linux Control Center ● Early development"
        )
        footer.setObjectName("muted")
        content_layout.addWidget(footer)

        # Automatic refresh every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(1000)

        self.update_metrics()

    def create_sidebar(self):
         sidebar = QFrame()
         sidebar.setObjectName("sidebar")
         sidebar.setFixedWidth(215)

         layout = QVBoxLayout(sidebar)
         layout.setContentsMargins(16, 24, 16, 18)
         layout.setSpacing(8)

         brand = QLabel("Linux Control")
         brand.setObjectName("brand")

         brand_subtitle = QLabel("CENTER")
         brand_subtitle.setObjectName("muted")

         layout.addWidget(brand)
         layout.addWidget(brand_subtitle)
         layout.addSpacing(28)

         section_label = QLabel("WORKSPACE")
         section_label.setObjectName("muted")
         layout.addWidget(section_label)
         layout.addSpacing(5)

         # Only Overview is implemented in this milestone.
         nav_items = [
              ("Overview", "▦"),
              ("Processes", "≡"),
              ("Storage", "▤"),
              ("Network", "↔"),
              ("Hardware", "◈"),
         ]

         for name, symbol in nav_items:
             button = QPushButton(f"{symbol}  {name}")
             button.setObjectName("nav_button")
             button.setProperty(
                   "selected", name == self.selected_page
             )
             button.setCursor(Qt.CursorShape.PointingHandCursor)

             if name != self.selected_page:
                 button.setEnabled(False)
                 button.setToolTip(
                        "This section will be implemented later"
                 )

             layout.addWidget(button)
         layout.addStretch()

         version = QLabel("Version 0.1.0")
         version.setObjectName("muted") 
         layout.addWidget(version)

         return sidebar

    @staticmethod
    def add_info_row(layout, label_text):
         row = QHBoxLayout()

         label = QLabel(label_text)
         label.setObjectName("body")

         value = QLabel("--")
         value.setObjectName("accent")
         value.setAlignment(
              Qt.AlignmentFlag.AlignRight
              | Qt.AlignmentFlag.AlignVCenter
         )

         row.addWidget(label)
         row.addStretch()
         row.addWidget(value)

         layout.addLayout(row)
         return value

    @staticmethod
    def format_uptime(seconds):
        seconds = max(0, int(seconds))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours >= 24:
            days, hours = divmod(hours, 24)
            return f"{days}d {hours:02}h {minutes:02}m"

        return f"{hours:02}h {minutes:02}m {seconds:02}s"

    def update_metrics(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=None)

            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024 ** 3)
            total_gb = memory.total / (1024 ** 3)

            self.cpu_card.update_metric(
                cpu_usage,
                f"{psutil.cpu_count() or 0} logical processors",
            )

            self.ram_card.update_metric(
                memory.percent,
                f"{used_gb:.1f} GB used of {total_gb:.1f} GB",
            )

            self.platform_value.setText(
                f"{platform.system()} {platform.release()}"
            )

            elapsed = time.monotonic() - self.start_time
            self.uptime_value.setText(
                self.format_uptime(elapsed)
            )

            self.interval_value.setText("Every 1 second")

            self.last_update_label.setText(
                time.strftime("Last update: %H:%M:%S")
            )

            self.status_label.setText("● Monitoring active")

        except (OSError, RuntimeError) as error:
            self.status_label.setText("● Monitoring error")
            self.last_update_label.setText(str(error))


# --------------------------------------------------
# Entry point
# ---------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Linux Control Center")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    window = LinuxControlCenter()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
     main()