from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect


class TestVoiceMateQuickMode:
    """E2E tests for VoiceMate quick mode
    (tryb błyskawiczny, pełny flow, timeouty,
    spinner, poprawne selektory, tylko realne przyciski)"""

    def wait_for_spinner_to_disappear(
        self,
        page: Page,
        spinner_texts: list[str],
        timeout: int = 40000,
    ) -> None:
        """Wait for spinner elements to disappear."""
        for spinner_text in spinner_texts:
            spinner = page.get_by_text(spinner_text, exact=False)
            try:
                if spinner.is_visible():
                    spinner.wait_for(state='hidden', timeout=timeout)
            except Exception:
                pass

    def test_quick_mode_full_flow(
        self,
        voicemate_page: Any,
        sample_pdf_file: str | Path,
    ) -> None:
        """Test the full flow of quick mode with PDF upload."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '⚡ Szybki podcast',
            exact=True,
        ).click()
        expect(
            voicemate_page.page.get_by_role(
                'heading',
                name='⚡ Tryb Błyskawiczny:'
                ' Wygeneruj cały podcast jednym kliknięciem',
            ),
        ).to_be_visible(timeout=10000)
        voicemate_page.page.locator(
            "input[type='file']",
        ).set_input_files(str(sample_pdf_file))
        generate_btn = voicemate_page.page.get_by_text(
            '🚀 Start – Wygeneruj podcast', exact=True,
        )
        expect(generate_btn).to_be_enabled()
        generate_btn.click()
        self.wait_for_spinner_to_disappear(
            voicemate_page.page, [
                '📥 Przetwarzanie treści...',
                '📝 Generowanie planu...',
                '🎙️ Generowanie treści podcastu...',
                '🔊 Generowanie audio...',
            ],
        )
        expect(
            voicemate_page.page.get_by_text(
                'w pełni wygenerowany', exact=False,
            ),
        ).to_be_visible(timeout=120000)
        audio_count = voicemate_page.page.locator('audio').count()
        print('Liczba elementów <audio> w DOM:', audio_count)
        voicemate_page.page.wait_for_selector('audio', timeout=10000)
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz tekst',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.get_by_role(
                'button', name='📥 Pobierz audio',
            ),
        ).to_be_visible()

    def test_quick_mode_pdf_upload(self, voicemate_page: Any, sample_pdf_file: str | Path) -> None:
        """Test the quick mode with PDF file upload."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text('⚡ Szybki podcast', exact=True).click()
        expect(
            voicemate_page.page.get_by_role(
                'heading',
                name='⚡ Tryb Błyskawiczny: '
                'Wygeneruj cały podcast jednym kliknięciem',
            ),
        ).to_be_visible(timeout=10000)
        voicemate_page.page.locator(
            "input[type='file']",
        ).set_input_files(str(sample_pdf_file))
        generate_btn = voicemate_page.page.get_by_text(
            '🚀 Start – Wygeneruj podcast', exact=True,
        )
        expect(generate_btn).to_be_enabled()

    def test_quick_mode_url_upload(self, voicemate_page: Any, sample_url: str) -> None:
        """Test the quick mode with URL input."""
        """This test simulates the process of entering a URL."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '⚡ Szybki podcast',
            exact=True,
        ).click()
        url_input = voicemate_page.page.locator(
            "input[placeholder='https://example.com']",
        )
        url_input.fill(sample_url)
        url_input.press('Enter')
        generate_btn = voicemate_page.page.get_by_text(
            '🚀 Start – Wygeneruj podcast', exact=True,
        )
        expect(generate_btn).to_be_enabled()

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

    def test_select_quick_mode(self, voicemate_page: Any) -> None:
        """Test the quick mode selection and UI elements."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.locator('text=⚡ Szybki podcast').click()
        expect(
            voicemate_page.page.locator(
                'text=⚡ Tryb Błyskawiczny: '
                'Wygeneruj cały podcast jednym kliknięciem',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.locator(
                'text=Wybierz plik',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.locator(
                'text=lub podaj URL',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.locator(
                'text=Wybierz styl:',
            ),
        ).to_be_visible()
        expect(
            voicemate_page.page.locator(
                'text=Wybierz silnik:',
            ),
        ).to_be_visible()

    def test_quick_mode_generate_podcast(
        self,
        voicemate_page: Any,
        sample_pdf_file: str | Path,
    ) -> None:
        """Test the quick mode podcast generation flow."""
        voicemate_page.wait_for_app_ready()
        voicemate_page.page.get_by_text(
            '⚡ Szybki podcast',
            exact=True,
        ).click()
        voicemate_page.page.locator(
            "input[type='file']",
        ).set_input_files(str(sample_pdf_file))
        voicemate_page.page.get_by_text(
            '🚀 Start – Wygeneruj podcast', exact=True,
        ).click()
        expect(
            voicemate_page.page.get_by_text(
                'w pełni wygenerowany', exact=False,
            ),
        ).to_be_visible(timeout=120000)
        expect(voicemate_page.page.locator('audio')).to_be_visible()
