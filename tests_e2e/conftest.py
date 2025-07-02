import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

STREAMLIT_PORT = 8501
STREAMLIT_URL = f'http://localhost:{STREAMLIT_PORT}'


@pytest.fixture(scope='session', autouse=True)
def start_streamlit_app():
    """
    Start the Streamlit app before tests and stop it after all tests are done.
    """

    env = os.environ.copy()
    process = subprocess.Popen(
        [
            sys.executable,
            '-m',
            'streamlit',
            'run',
            'app.py',
            '--server.port',
            str(
                STREAMLIT_PORT,
            ),
        ],
        env=env,
    )

    timeout = 60
    start = time.time()
    while True:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                break
        except Exception:
            pass
        if time.time() - start > timeout:
            process.terminate()
            raise RuntimeError('Streamlit app did not start in time.')
        time.sleep(1)

    yield

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def voicemate_page(page):
    """
    Fixture to create a VoiceMatePage instance for testing."""

    class VoiceMatePage:
        def __init__(self, page):
            self.page = page

        def wait_for_app_ready(self):
            self.page.goto('http://localhost:8501', timeout=30000)

            self.page.wait_for_selector(
                'text=Rozpocznij krok po kroku',
                timeout=20000,
            )
            self.page.wait_for_selector(
                'text=Szybki podcast',
                timeout=20000,
            )

    return VoiceMatePage(page)


@pytest.fixture
def sample_pdf_file():
    """Fixture to provide a sample PDF file path for testing."""
    return str(Path('test_data') / 'sample.pdf')


@pytest.fixture
def sample_url():
    """Fixture to provide a sample URL for testing."""
    return 'https://example.com'
