import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT_PATH = os.path.join(os.path.dirname(
    __file__), '../../src/file_parser/url2pdf.py')
SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)


@pytest.fixture
def temp_output_pdf():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_pdf = os.path.join(temp_dir, 'output.pdf')
        yield output_pdf


@pytest.mark.skipif('DISPLAY' not in os.environ and sys.platform != 'win32', reason='Requires GUI environment for PyQt5')
def test_url2pdf_success(temp_output_pdf):
    # Używamy prostego, publicznego URL (np. strona główna Google)
    url = 'https://www.example.com/'
    result = subprocess.run([
        sys.executable, SCRIPT_PATH, url, temp_output_pdf
    ], capture_output=True, text=True)
    assert result.returncode == 0, f'stderr: {result.stderr}'
    assert os.path.exists(temp_output_pdf)
    assert os.path.getsize(temp_output_pdf) > 0


@pytest.mark.skipif('DISPLAY' not in os.environ and sys.platform != 'win32', reason='Requires GUI environment for PyQt5')
def test_url2pdf_invalid_url(temp_output_pdf):
    url = 'http://nonexistent.domain.abc/'
    result = subprocess.run([
        sys.executable, SCRIPT_PATH, url, temp_output_pdf
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert not os.path.exists(temp_output_pdf)
    assert 'Failed to load page' in result.stderr or 'PDF creation failed' in result.stderr or 'ERR_NAME_NOT_RESOLVED' in result.stderr
