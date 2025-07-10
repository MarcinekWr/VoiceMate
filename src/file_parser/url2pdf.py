"""
This script provides a function to convert a URL to a PDF file using PyQt5's QtWebEngine, suitable for headless conversion in automation workflows.
"""
from __future__ import annotations

import gc
import sys

from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import QEventLoop, QTimer, QUrl
from PyQt5.QtGui import QPageLayout, QPageSize
from PyQt5.QtWidgets import QApplication

from src.utils.logging_config import get_request_id, get_session_logger


def convert_url_to_pdf(url: str, output_path: str, request_id: str | None = None) -> None:
    """
    Convert a URL to a PDF file using PyQt5's QtWebEngine.

    Args:
        url (str): The URL to convert to PDF.
        output_path (str): Path where the PDF will be saved.
        request_id (str, optional): Unique request identifier for logging. If None, a new one is generated.

    Raises:
        SystemExit: If the page fails to load or PDF generation fails.
    """
    request_id = request_id or get_request_id()
    logger = get_session_logger(request_id)
    logger.info(f"📥 Rozpoczynam konwersję URL na PDF: {url}")
    logger.info(f"📤 Ścieżka wyjściowa: {output_path}")

    app = QApplication(sys.argv)
    web_view = QtWebEngineWidgets.QWebEngineView()
    web_view.setZoomFactor(1)

    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.A4))
    layout.setOrientation(QPageLayout.Portrait)

    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(
        lambda: (
            logger.error("❌ Timeout: generowanie PDF-a trwało zbyt długo"),
            loop.quit(),
            sys.exit(1),
        )
    )

    def handle_load_finished(ok: bool) -> None:
        """
        Handle the load finished event for the web page.

        Args:
            ok (bool): True if the page loaded successfully, False otherwise.

        Raises:
            SystemExit: If the page fails to load.
        """
        if not ok:
            logger.error(f"❌ Nie udało się załadować strony: {url}")
            loop.quit()
            sys.exit(1)
        logger.info(f"🌍 Strona załadowana pomyślnie, drukowanie do: {output_path}")
        web_view.page().printToPdf(output_path, layout)

    def handle_pdf_finished(path: str, success: bool) -> None:
        """
        Handle the PDF printing finished event.

        Args:
            path (str): Path where the PDF was saved.
            success (bool): True if PDF was saved successfully, False otherwise.

        Raises:
            SystemExit: If PDF saving fails.
        """
        if success:
            logger.info(f"✅ PDF zapisany pomyślnie do: {path}")
        else:
            logger.error(f"❌ Nie udało się zapisać PDF-a do: {path}")
            sys.exit(1)
        loop.quit()

    web_view.loadFinished.connect(handle_load_finished)
    web_view.page().pdfPrintingFinished.connect(handle_pdf_finished)
    web_view.load(QUrl(url))

    timer.start(30000)  # 30 sekund timeout
    loop.exec_()

    web_view.page().deleteLater()
    web_view.deleteLater()
    gc.collect()
    app.quit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('\u274c Usage: python url2pdf.py <URL> <output_path>')
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2]
    convert_url_to_pdf(url, output_path)
