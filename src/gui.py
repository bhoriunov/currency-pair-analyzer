"""Graphical user interface for the Currency Pair Analyzer application."""
import csv

import matplotlib as mpl
import matplotlib.dates as mdates
import mplfinance as mpf
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis import analyze_rates
from api_client import fetch_exchange_rates

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "axes.titlesize": 16,
    "axes.titleweight": "semibold",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})


INTERVAL_RANGES = {
    "1min": ["1h", "6h", "24h"],
    "5min": ["1h", "6h", "24h", "7d", "14d"],
    "15min": ["6h", "24h", "7d", "14d", "30d"],
    "1h": ["24h", "7d", "30d", "60d", "90d"],
}


class MainWindow(QMainWindow):
    """Main application window for loading, visualizing, and analyzing FX data."""
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Currency Pair Analyzer")
        self.resize(1100, 750)

        # Apply PyQt widget styling for the main application window.
        # The stylesheet was created with AI-assisted help.

        self.setStyleSheet(
            """
            QWidget {
                background: #F5F7FB;
                font-size: 14px;
                color: #1E293B;
            }
            
            QComboBox, QTextEdit, QTableWidget {
                background: #FFFFFF;
                border: 1px solid #D9E1EC;
                border-radius: 8px;
                padding: 4px;
            }
            QComboBox {
                padding: 4px 28px 4px 8px;
                min-height: 24px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border: none;
                background: #FFFFFF;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #D1DAE6;
                border-radius: 10px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                background: #F8FAFC;
            }
            QPushButton:disabled {
                background: #efefef;
                color: #999999;
            }
            
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                border: 1px solid #D9E1EC;
                selection-background-color: #E8F1FF;
                selection-color: #1E293B;
                outline: 0;
            }

            QComboBox QAbstractItemView::item:hover {
                background: #F3F7FF;
                color: #1E293B;
            }

            QComboBox QAbstractItemView::item:selected {
                background: #E8F1FF;
                color: #1E293B;
            }         
        """
        )

        self.current_records: list[dict] = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        self.base_label = QLabel("Base currency:")
        self.base_combo = QComboBox()
        self.base_combo.addItems(["EUR", "USD", "GBP", "CZK", "JPY", "CHF"])

        self.target_label = QLabel("Target currency:")
        self.target_combo = QComboBox()
        self.target_combo.addItems(["USD", "EUR", "GBP", "CZK", "JPY", "CHF"])

        self.interval_label = QLabel("Interval:")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(list(INTERVAL_RANGES.keys()))

        self.range_label = QLabel("Range:")
        self.range_combo = QComboBox()

        self.chart_type_label = QLabel("Chart type:")
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Line", "Candlestick"])

        self.load_button = QPushButton("Load data")
        self.export_button = QPushButton("Export CSV")
        self.export_button.setEnabled(False)

        self.load_button.setStyleSheet(
            """
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #1D4ED8;
            }
        """
        )

        controls_layout.addWidget(self.base_label)
        controls_layout.addWidget(self.base_combo)
        controls_layout.addWidget(self.target_label)
        controls_layout.addWidget(self.target_combo)
        controls_layout.addWidget(self.interval_label)
        controls_layout.addWidget(self.interval_combo)
        controls_layout.addWidget(self.range_label)
        controls_layout.addWidget(self.range_combo)
        controls_layout.addWidget(self.chart_type_label)
        controls_layout.addWidget(self.chart_type_combo)
        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.export_button)

        self.interval_combo.currentTextChanged.connect(self.update_range_options)
        self.update_range_options(self.interval_combo.currentText())

        self.figure = Figure(facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(350)

        self.chart_container = QWidget()
        self.chart_container.setStyleSheet(
            """
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
        """
        )

        chart_layout = QVBoxLayout()
        chart_layout.setContentsMargins(10, 10, 10, 10)
        chart_layout.addWidget(self.canvas)
        self.chart_container.setLayout(chart_layout)

        self._is_panning = False
        self._pan_start = None
        self._xlim_on_press = None
        self._ylim_on_press = None

        self._mpl_cid_scroll = self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self._mpl_cid_press = self.canvas.mpl_connect(
            "button_press_event", self.on_press
        )
        self._mpl_cid_release = self.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self._mpl_cid_move = self.canvas.mpl_connect(
            "motion_notify_event", self.on_move
        )
        self._mpl_cid_dblclick = self.canvas.mpl_connect(
            "button_press_event", self.on_double_click
        )

        self.selected_price_label = QLabel("Selected price: -")
        self.selected_price_label.setStyleSheet(
            "color: #1E293B; padding: 4px; font-weight: 600;"
        )

        self._hover_annotation = None
        self._press_pos = None

        self._default_xlim = None
        self._default_ylim = None

        content_layout = QGridLayout()
        main_layout.addLayout(content_layout)

        self.stats_label = QLabel(
            "Average: ...\n"
            "Minimum: ...\n"
            "Maximum: ...\n"
            "Last rate: ...\n"
            "Total change: ...\n"
            "Percent change: ...\n"
            "Volatility: ...\n"
            "Risk level: ..."
        )

        self.stats_label.setStyleSheet(
            """
                QLabel {
                    background: #FFFFFF;
                    border: 1px solid #d8d8d8;
                    border-radius: 8px;
                    padding: 12px;
                    color: #0F172A;
                }
            """
        )

        content_layout.addWidget(self.chart_container, 0, 0)
        content_layout.addWidget(self.stats_label, 0, 1)

        main_layout.addWidget(self.selected_price_label)

        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setPlaceholderText("Summary will be displayed here.")
        main_layout.addWidget(self.summary_box)
        self.summary_box.setMaximumHeight(80)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Datetime", "Open", "High", "Low", "Close"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.table)
        self.table.setMaximumHeight(180)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.error_label)

        self.load_button.clicked.connect(self.load_data)
        self.export_button.clicked.connect(self.export_csv)

        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        content_layout.setHorizontalSpacing(18)
        content_layout.setVerticalSpacing(10)
        content_layout.setColumnStretch(0, 4)
        content_layout.setColumnStretch(1, 2)

        self._data_xlim = None
        self._data_ylim = None

        self._last_hover_pos = None

    def load_data(self) -> None:
        """Load exchange rate data, compute statistics, and update the GUI."""
        self.error_label.setText("")
        self.error_label.setStyleSheet("color: red;")

        base = self.base_combo.currentText()
        target = self.target_combo.currentText()
        interval = self.interval_combo.currentText()
        range_value = self.range_combo.currentText()
        chart_type = self.chart_type_combo.currentText()

        if base == target:
            self.error_label.setText("Base and target currencies must be different.")
            return

        try:
            records = fetch_exchange_rates(base, target, interval, range_value)
            closes = [record["close"] for record in records]
            stats = analyze_rates(closes)

            self.current_records = records
            self.export_button.setEnabled(True)

            self.stats_label.setText(
                f"Pair: {base}/{target}\n"
                f"Interval: {interval}\n"
                f"Range: {range_value}\n"
                f"Chart type: {chart_type}\n"
                f"Points loaded: {len(records)}\n\n"
                f"Average: {stats['average']:.4f}\n"
                f"Minimum: {stats['minimum']:.4f}\n"
                f"Maximum: {stats['maximum']:.4f}\n"
                f"Last rate: {stats['last_rate']:.4f}\n"
                f"Total change: {stats['total_change']:+.4f}\n"
                f"Percent change: {stats['percent_change']:+.2f}%\n"
                f"Volatility: {stats['volatility']:.6f}\n"
                f"Risk level: {stats['risk_level']}"
            )

            self.summary_box.setPlainText(stats["summary"])
            self.fill_table(records)
            self.update_chart(records, base, target, interval, range_value, chart_type)

        except Exception as e:
            self.error_label.setText(f"Error: {e}")
            self.export_button.setEnabled(False)
            self.current_records = []

            self.stats_label.setText(
                "Pair: -\n"
                "Interval: -\n"
                "Range: -\n"
                "Chart type: -\n"
                "Points loaded: -\n\n"
                "Average: -\n"
                "Minimum: -\n"
                "Maximum: -\n"
                "Last rate: -\n"
                "Total change: -\n"
                "Percent change: -\n"
                "Volatility: -\n"
                "Risk level: -"
            )

            self.summary_box.clear()
            self.table.setRowCount(0)
            self.selected_price_label.setText("Selected price: -")

            self.figure.clear()
            self.canvas.draw()

            self._hover_annotation = None
            self._press_pos = None
            self._pan_start = None
            self._xlim_on_press = None
            self._ylim_on_press = None
            self._default_xlim = None
            self._default_ylim = None
            self._data_xlim = None
            self._data_ylim = None
            self._last_hover_pos = None
            self._is_panning = False

    def fill_table(self, records: list[dict]) -> None:
        """Fill the table widget with loaded OHLC records."""
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(record["datetime"].strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.table.setItem(row, 1, QTableWidgetItem(f"{record['open']:.4f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{record['high']:.4f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{record['low']:.4f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record['close']:.4f}"))

    def update_chart(
        self,
        records: list[dict],
        base: str,
        target: str,
        interval: str,
        range_value: str,
        chart_type: str,
    ) -> None:
        """Render the selected dataset as either a line or candlestick chart."""
        self.figure.clear()

        if chart_type == "Line":
            dates = [record["datetime"] for record in records]
            closes = [record["close"] for record in records]

            ax = self.figure.add_subplot(111)

            ax.set_facecolor("white")
            ax.title.set_fontsize(16)
            ax.xaxis.label.set_fontsize(11)
            ax.yaxis.label.set_fontsize(11)
            ax.tick_params(axis="x", labelsize=10)
            ax.tick_params(axis="y", labelsize=10)

            self._hover_annotation = ax.annotate(
                "",
                xy=(0, 0),
                xytext=(12, 12),
                textcoords="offset points",
                bbox=dict(
                    boxstyle="round,pad=0.3", fc="white", ec="#CBD5E1", alpha=0.95
                ),
                fontsize=9,
            )

            self._hover_annotation.set_visible(False)

            use_markers = len(records) <= 100
            if use_markers:
                ax.plot(dates, closes, marker="o", markersize=3, linewidth=1.6)
            else:
                ax.plot(dates, closes, linewidth=1.6)

            ax.set_title(f"{base}/{target} · {interval} · {range_value}", pad=8)
            ax.set_xlabel("Datetime")
            ax.set_ylabel("Rate", labelpad=12)
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
            ax.yaxis.set_major_formatter(FormatStrFormatter("%.6f"))

            locator = mdates.AutoDateLocator()
            ax.xaxis.set_major_locator(locator)

            if range_value in {"1h", "6h"}:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            elif range_value == "24h":
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))

            ax.set_xlim(min(dates), max(dates))

            y_min = min(closes)
            y_max = max(closes)
            padding = (y_max - y_min) * 0.1 if y_max > y_min else 0.001
            ax.set_ylim(y_min - padding, y_max + padding)

            if range_value == "24h":
                ax.tick_params(axis="x", labelsize=8, labelrotation=20)
            else:
                ax.tick_params(axis="x", labelsize=9)

            self._default_xlim = ax.get_xlim()
            self._default_ylim = ax.get_ylim()
            self._data_xlim = ax.get_xlim()
            self._data_ylim = (y_min - padding, y_max + padding)

            self.figure.subplots_adjust(left=0.10, right=0.88, top=0.90, bottom=0.18)
            self.canvas.draw()
            return

        df = pd.DataFrame(records)
        df = df.set_index("datetime")
        df = df.rename(
            columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}
        )

        market_colors = mpf.make_marketcolors(
            up="#00A676",
            down="#CC444B",
            wick="inherit",
            edge="inherit",
            volume="inherit",
        )

        style = mpf.make_mpf_style(
            base_mpf_style="yahoo",
            marketcolors=market_colors,
            facecolor="#ffffff",
            figcolor="#ffffff",
            gridcolor="#e5e7eb",
            gridstyle="-",
        )

        ax = self.figure.add_subplot(111)
        ax.set_facecolor("white")
        ax.title.set_fontsize(14)
        ax.xaxis.label.set_fontsize(11)
        ax.yaxis.label.set_fontsize(11)
        ax.tick_params(axis="x", labelsize=10)
        ax.tick_params(axis="y", labelsize=10)

        self._hover_annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#CBD5E1", alpha=0.95),
            fontsize=9,
        )

        self._hover_annotation.set_visible(False)

        if range_value in {"1h", "6h"}:
            dt_format = "%H:%M"
        elif range_value == "24h":
            dt_format = "%d.%m %H:%M"
        else:
            dt_format = "%d.%m"

        mpf.plot(
            df,
            type="candle",
            ax=ax,
            style=style,
            datetime_format=dt_format,
            xrotation=0,
            show_nontrading=False,
            tight_layout=False,
        )

        ax.set_title(f"{base}/{target} · {interval} · {range_value}", pad=8)
        ax.set_xlabel("Datetime")
        ax.set_ylabel("Price", labelpad=12)
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.6f"))

        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=9)

        self._default_xlim = ax.get_xlim()
        self._default_ylim = ax.get_ylim()
        self._data_xlim = ax.get_xlim()
        self._data_ylim = ax.get_ylim()

        self.figure.subplots_adjust(left=0.10, right=0.90, top=0.90, bottom=0.20)
        self.canvas.draw()

    def export_csv(self) -> None:
        """Export the currently loaded OHLC records to a CSV file."""
        if not self.current_records:
            self.error_label.setText("No data available for export.")
            self.error_label.setStyleSheet("color: red;")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV file", "exchange_rates.csv", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Datetime", "Open", "High", "Low", "Close"])

                for record in self.current_records:
                    writer.writerow(
                        [
                            record["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                            f"{record['open']:.4f}",
                            f"{record['high']:.4f}",
                            f"{record['low']:.4f}",
                            f"{record['close']:.4f}",
                        ]
                    )

            self.error_label.setText("CSV export completed successfully.")
            self.error_label.setStyleSheet("color: green;")

        except Exception as e:
            self.error_label.setText(f"Error: {e}")
            self.error_label.setStyleSheet("color: red;")

    def update_range_options(self, interval: str) -> None:
        """Update available range options for the selected interval."""
        current_range = self.range_combo.currentText()

        self.range_combo.clear()
        self.range_combo.addItems(INTERVAL_RANGES[interval])

        index = self.range_combo.findText(current_range)
        if index >= 0:
            self.range_combo.setCurrentIndex(index)

    def on_scroll(self, event) -> None:
        """Zoom the chart around the current mouse position.
        This method updates both x and y axis limits while keeping the visible
        area inside the loaded data bounds.
        The zoom interaction logic was implemented with AI-assisted help.
        """
        if event.inaxes is None:
            return
        if self._data_xlim is None or self._data_ylim is None:
            return

        ax = event.inaxes

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return

        scale_factor = 0.9 if event.button == "up" else 1.1

        cur_width = cur_xlim[1] - cur_xlim[0]
        cur_height = cur_ylim[1] - cur_ylim[0]

        new_width = cur_width * scale_factor
        new_height = cur_height * scale_factor

        rel_x = (cur_xlim[1] - xdata) / cur_width
        rel_y = (cur_ylim[1] - ydata) / cur_height

        new_left = xdata - new_width * (1 - rel_x)
        new_right = xdata + new_width * rel_x

        new_bottom = ydata - new_height * (1 - rel_y)
        new_top = ydata + new_height * rel_y

        data_left, data_right = self._data_xlim
        data_bottom, data_top = self._data_ylim

        max_width = data_right - data_left
        max_height = data_top - data_bottom

        if new_width >= max_width:
            new_left, new_right = data_left, data_right
        else:
            if new_left < data_left:
                shift = data_left - new_left
                new_left += shift
                new_right += shift
            if new_right > data_right:
                shift = new_right - data_right
                new_left -= shift
                new_right -= shift

        if new_height >= max_height:
            new_bottom, new_top = data_bottom, data_top
        else:
            if new_bottom < data_bottom:
                shift = data_bottom - new_bottom
                new_bottom += shift
                new_top += shift
            if new_top > data_top:
                shift = new_top - data_top
                new_bottom -= shift
                new_top -= shift

        ax.set_xlim(new_left, new_right)
        ax.set_ylim(new_bottom, new_top)

        self.canvas.draw_idle()

    def on_press(self, event) -> None:
        """Store initial mouse position and axis limits for possible dragging."""
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        if event.xdata is None or event.ydata is None:
            return

        self._press_pos = (event.xdata, event.ydata)
        self._pan_start = (event.xdata, event.ydata)
        self._xlim_on_press = event.inaxes.get_xlim()
        self._ylim_on_press = event.inaxes.get_ylim()
        self._is_panning = False

    def on_release(self, event) -> None:
        """Finish dragging and store the selected price on a click."""
        self._is_panning = False
        self._pan_start = None
        self._xlim_on_press = None
        self._ylim_on_press = None

        if (
            event.inaxes is not None
            and event.xdata is not None
            and event.ydata is not None
            and self._press_pos is not None
        ):
            dx = abs(event.xdata - self._press_pos[0])
            dy = abs(event.ydata - self._press_pos[1])
            if dx < 1e-6 and dy < 1e-6:
                self.selected_price_label.setText(f"Selected price: {event.ydata:.5f}")

        self._press_pos = None

    def on_move(self, event) -> None:
        """Handle mouse movement over the chart.
        This method updates the hover price annotation and supports chart panning
        after a drag gesture is detected, while keeping the view inside data bounds.
        The movement and panning logic was implemented with AI-assisted help.
        """
        if self._hover_annotation is not None:
            if (
                not self._is_panning
                and event.inaxes is not None
                and event.xdata is not None
                and event.ydata is not None
            ):
                if self._last_hover_pos is None:
                    should_update_hover = True
                else:
                    last_x, last_y = self._last_hover_pos
                    should_update_hover = (
                        abs(event.xdata - last_x) > 1e-4
                        or abs(event.ydata - last_y) > 1e-4
                    )

                if should_update_hover:
                    self._hover_annotation.xy = (event.xdata, event.ydata)
                    self._hover_annotation.set_text(f"Price: {event.ydata:.5f}")
                    self._hover_annotation.set_visible(True)
                    self._last_hover_pos = (event.xdata, event.ydata)
                    self.canvas.draw_idle()
            else:
                if self._hover_annotation.get_visible():
                    self._hover_annotation.set_visible(False)
                    self.canvas.draw_idle()
                self._last_hover_pos = None

        if event.inaxes is None or self._pan_start is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        if self._data_xlim is None or self._data_ylim is None:
            return

        ax = event.inaxes

        dx = event.xdata - self._pan_start[0]
        dy = event.ydata - self._pan_start[1]

        if not self._is_panning:
            if abs(dx) > 5e-4 or abs(dy) > 5e-4:
                self._is_panning = True
            else:
                return

        new_left = self._xlim_on_press[0] - dx
        new_right = self._xlim_on_press[1] - dx

        new_bottom = self._ylim_on_press[0] - dy
        new_top = self._ylim_on_press[1] - dy

        data_left, data_right = self._data_xlim
        data_bottom, data_top = self._data_ylim

        width = new_right - new_left
        height = new_top - new_bottom

        if new_left < data_left:
            new_left = data_left
            new_right = data_left + width
        if new_right > data_right:
            new_right = data_right
            new_left = data_right - width

        if new_bottom < data_bottom:
            new_bottom = data_bottom
            new_top = data_bottom + height
        if new_top > data_top:
            new_top = data_top
            new_bottom = data_top - height

        ax.set_xlim(new_left, new_right)
        ax.set_ylim(new_bottom, new_top)

        self.canvas.draw_idle()

    def on_double_click(self, event) -> None:
        """Reset the chart view to the default axis limits on double click."""
        if not getattr(event, "dblclick", False):
            return
        if event.inaxes is None:
            return
        if self._default_xlim is None or self._default_ylim is None:
            return

        ax = event.inaxes
        ax.set_xlim(self._default_xlim)
        ax.set_ylim(self._default_ylim)
        self.canvas.draw_idle()
