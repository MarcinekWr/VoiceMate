from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../src/file_parser/url2pdf.py')
)


@pytest.mark.skipif(
    'DISPLAY' not in os.environ and sys.platform != 'win32',
    reason='Requires GUI environment for PyQt5',
)
def test_url2pdf_usage_message():
    """Testuje wywołanie bez argumentów - powinna pojawić się informacja o użyciu."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH],
        capture_output=True,
        text=True,
        env={**os.environ, 'PYTHONPATH': os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../'))},
    )
    assert result.returncode != 0
    assert 'Usage: python url2pdf.py <URL> <output_path>' in result.stdout or 'Usage: python url2pdf.py <URL> <output_path>' in result.stderr


@pytest.mark.skipif(
    'DISPLAY' not in os.environ and sys.platform != 'win32',
    reason='Requires GUI environment for PyQt5',
)
def test_url2pdf_output_file_created_and_not_empty():
    """Testuje, czy plik PDF jest tworzony i nie jest pusty dla poprawnego URL."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_pdf = os.path.join(temp_dir, 'output.pdf')
        url = 'https://www.example.com/'
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, url, output_pdf],
            capture_output=True,
            text=True,
            env={**os.environ, 'PYTHONPATH': os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../'))},
        )
        assert result.returncode == 0, f'stderr: {result.stderr}'
        assert os.path.exists(output_pdf)
        assert os.path.getsize(output_pdf) > 0
