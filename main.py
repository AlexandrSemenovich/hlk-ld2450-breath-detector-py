import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import QThread

from core.config import UI, STYLESHEET, TYPO
from models.serial_source import SerialWorker
from viewmodels.settings_vm import SettingsViewModel
from viewmodels.connection_vm import ConnectionViewModel
from viewmodels.heatmap_vm import HeatmapViewModel
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont(TYPO.font_family, TYPO.font_size))
    app.setStyleSheet(STYLESHEET)

    settings_vm = SettingsViewModel()
    heatmap_vm = HeatmapViewModel(settings_vm)

    worker = SerialWorker()
    thread = QThread()
    worker.moveToThread(thread)
    thread.start()

    connection_vm = ConnectionViewModel(worker)

    window = MainWindow(connection_vm, settings_vm, heatmap_vm)
    window.show()

    window.heatmap_view.start()

    info_panel = window.info_panel

    worker.frameReady.connect(heatmap_vm.ingest)
    worker.frameReady.connect(info_panel.update_frame)
    heatmap_vm.updated.connect(lambda payload: info_panel.update_stats(payload["stats"]))

    window.clear_btn.clicked.connect(heatmap_vm.clear)
    window.clear_btn.clicked.connect(window.heatmap_view.clear)

    def _shutdown():
        connection_vm.request_finish()
        thread.quit()
        thread.wait()

    app.aboutToQuit.connect(_shutdown)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
