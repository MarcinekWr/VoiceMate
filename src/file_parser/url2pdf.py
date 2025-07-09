from __future__ import annotations

import gc
import logging
import sys

from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import QEventLoop, QTimer, QUrl
from PyQt5.QtGui import QPageLayout, QPageSize
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def convert_url_to_pdf(url: str, output_path: str) -> None:
    """Convert a URL to a PDF file."""
    app = QApplication(sys.argv)
    web_view = QtWebEngineWidgets.QWebEngineView()
    web_view.setZoomFactor(1)
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.A4))
    layout.setOrientation(QPageLayout.Portrait)
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)

    def handle_load_finished(ok: bool) -> None:
        """Handle the load finished event."""
        if not ok:
            logger.error(f'Failed to load URL: {url}')
            loop.quit()
            sys.exit(1)
        web_view.page().printToPdf(output_path, layout)

    def handle_pdf_finished(path: str, success: bool) -> None:
        loop.quit()
        if not success:
            logger.error(f'Failed to save PDF to {path}')
            sys.exit(1)

    web_view.loadFinished.connect(handle_load_finished)
    web_view.page().pdfPrintingFinished.connect(handle_pdf_finished)
    web_view.load(QUrl(url))
    timer.start(30000)
    loop.exec_()
    web_view.page().deleteLater()
    web_view.deleteLater()
    gc.collect()
    app.quit()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        logger.error('Usage: python url2pdf.py <URL> <output_path>')
        sys.exit(1)
    convert_url_to_pdf(sys.argv[1], sys.argv[2])
