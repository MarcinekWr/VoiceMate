from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect


class TestVoiceMateStepByStep:
    """E2E tests for VoiceMate step-by-step mode
    (dłuższe timeouty, czekanie na nagłówek audio,
    debug <audio>, poprawka strict mode dla przycisków,
    poprawka komunikatu końcowego)"""

    def wait_for_spinner_to_disappear(
        self,
        page: Page,
        spinner_texts: list[str],
        timeout: int = 40000,
    ) -> None:
        """Wait for spinner elements to disappear on the page."""
        for spinner_text in spinner_texts:
            spinner = page.get_by_text(spinner_text, exact=False)
            try:
                if spinner.is_visible():
                    spinner.wait_for(state='hidden', timeout=timeout)
            except Exception:
                pass

    def test_homepage_display(self, voicemate_page: Any) -> None:
        """Test if the homepage displays correctly."""
        voicemate_page.wait_for_app_ready()
        expect(
            voicemate_page.page.get_by_text(
                '🚀 Rozpocznij krok po kroku', exact=True,
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_text(
                '⚡ Szybki podcast', exact=True,
            ),
        ).to_be_visible()

    def test_step_by_step_full_flow(self, voicemate_page: Any, sample_pdf_file: str | Path) -> None:
        """Test the full step-by-step flow with a sample PDF file."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '🚀 Rozpocznij krok po kroku', exact=True,
        ).click()
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📁 Wczytaj plik',
            ),
        ).to_be_visible(timeout=10000)
        voicemate_page.page.locator(
            "input[type='file']",
        ).set_input_files(str(sample_pdf_file))
        process_btn = voicemate_page.page.get_by_text(
            '🚀 Przetwórz', exact=True,
        )
        expect(process_btn).to_be_enabled()
        process_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Przetwarzanie w toku...',
                '🔄 Przetwarzanie pliku i wydobywanie treści...',
            ],
        )
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📝 Krok 2: Generuj plan podcastu',
            ),
        )\
            .to_be_visible(timeout=30000)
        plan_btn = voicemate_page.page.get_by_text(
            '📝 Generuj plan', exact=True,
        )
        expect(plan_btn).to_be_enabled()
        plan_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Generowanie planu...',
                '🧠 Analizuję treść i tworzę plan podcastu...',
            ],
        )
        expect(
            voicemate_page.page.get_by_role(
                'heading',
                name='🎙️ Krok 3: Generuj podcast i wybierz silnik audio',
            ),
        )\
            .to_be_visible(timeout=120000)
        podcast_btn = voicemate_page.page.get_by_text(
            '🎙️ Generuj podcast', exact=True,
        )
        expect(podcast_btn).to_be_enabled()
        podcast_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Generowanie tekstu podcastu...',
                '🎙️ Tworzę tekst podcastu',
            ],
        )
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='🎵 Krok 4: Generuj audio',
            ),
        ).\
            to_be_visible(timeout=120000)
        audio_btn = voicemate_page.page.get_by_text(
            '🎵 Generuj audio', exact=True,
        )
        expect(audio_btn).to_be_enabled()
        audio_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Generowanie audio...',
                '🎵 Generuję audio za pomocą',
            ],
        )
        expect(
            voicemate_page.page.get_by_text(
                '🎧 Wygenerowane audio', exact=False,
            ),
        ).to_be_visible(timeout=120000)
        audio_count = voicemate_page.page.locator('audio').count()
        print('Liczba elementów <audio> w DOM:', audio_count)
        voicemate_page.page.wait_for_selector('audio', timeout=10000)
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz plan',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz podcast',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz JSON',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz audio',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_text(
                'zakończony pomyślnie', exact=False,
            ),
        ).to_be_visible()

    def test_step_by_step_pdf_upload(self,
                                     voicemate_page: Any,
                                     sample_pdf_file: str | Path) -> None:
        """Test the step-by-step flow with a sample PDF file.
        This test simulates the process of uploading a PDF file"""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '🚀 Rozpocznij krok po kroku', exact=True,
        ).click()
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📁 Wczytaj plik',
            ),
        ).to_be_visible(timeout=10000)
        voicemate_page.page.locator(
            "input[type='file']",
        ).set_input_files(str(sample_pdf_file))
        process_btn = voicemate_page.page.get_by_text(
            '🚀 Przetwórz', exact=True,
        )
        expect(process_btn).to_be_enabled()
        process_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Przetwarzanie w toku...',
                '🔄 Przetwarzanie pliku i wydobywanie treści...',
            ],
        )
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📝 Krok 2: Generuj plan podcastu',
            ),
        ).\
            to_be_visible(timeout=30000)

    def test_step_by_step_url_upload(self, voicemate_page: Any, sample_url: str) -> None:
        """Test the step-by-step flow with a sample URL.
        This test simulates the process of uploading a URL."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '🚀 Rozpocznij krok po kroku', exact=True,
        ).click()
        url_input = voicemate_page.page.locator(
            "input[placeholder='https://example.com/article']",
        )
        url_input.fill(sample_url)
        url_input.press('Enter')
        process_btn = voicemate_page.page.get_by_text(
            '🚀 Przetwórz', exact=True,
        )
        expect(process_btn).to_be_enabled()
        process_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '🔄 Przetwarzanie w toku...',
                '🔄 Przetwarzanie pliku i wydobywanie treści...',
            ],
        )
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📝 Krok 2: Generuj plan podcastu',
            ),
        ).\
            to_be_visible(timeout=30000)

    def test_select_step_by_step_mode(self, voicemate_page: Any) -> None:
        """Test the step-by-step mode selection and UI elements."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '🚀 Rozpocznij krok po kroku', exact=True,
        ).click()
        expect(
            voicemate_page.page.get_by_role(
                'heading', name='📁 Wczytaj plik',
            ),
        ).to_be_visible(timeout=10000)
