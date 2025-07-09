# VoiceMate

VoiceMate is a modular application for converting documents into audio using advanced text-to-speech (TTS) services. It leverages Streamlit for the UI, supports PDF parsing and image extraction, and integrates with Azure and ElevenLabs for high-quality audio output. The codebase is organized for extensibility, with clear session management, logging, and cloud integration.

## Techniques Used

- **Session State Management**: Uses [Streamlit session state](https://docs.streamlit.io/library/api-reference/session-state) to persist user context and progress.
- **Per-Session Logging**: Creates a logger for each session and uploads logs to [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/).
- **Modular UI Rendering**: Each UI step is a separate module for maintainability and clarity.
- **Environment Variable Loading**: Uses [python-dotenv](https://pypi.org/project/python-dotenv/) for configuration.
- **PDF Parsing and Image Extraction**: Handles complex PDF content, including images and tables.

## Notable Libraries and Technologies

- [Streamlit](https://streamlit.io/): Web UI framework.
- [python-dotenv](https://pypi.org/project/python-dotenv/): Loads environment variables from `.env` files.
- [Azure Blob Storage SDK](https://pypi.org/project/azure-storage-blob/): For cloud log uploads.
- [PyPDF2](https://pypi.org/project/PyPDF2/): PDF parsing (implied by file names).
- [ElevenLabs TTS](https://elevenlabs.io/): Text-to-speech synthesis.
- [Docker](https://www.docker.com/): Containerization.
- [pytest](https://docs.pytest.org/en/stable/): Testing framework.
- [pre-commit](https://pre-commit.com/): Code quality enforcement.

## Project Structure

```
.
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
├── assets/
├── extracted_content/
├── log_folder/
│   └── logs/
├── src/
│   ├── common/
│   ├── file_parser/
│   ├── logic/
│   ├── prompts/
│   ├── services/
│   ├── ui/
│   │   └── steps/
│   ├── utils/
│   ├── workflow/
│   └── voicemate.egg-info/
├── tests/
├── tests_e2e/
├── test_data/
├── .github/
```

### Directory Descriptions

- **src/common/**: Shared constants and configuration.
- **src/file_parser/**: PDF and file parsing utilities.
- **src/logic/**: TTS and podcast logic.
- **src/prompts/**: Prompt templates for LLM and TTS.
- **src/services/**: Service layer for integrations.
- **src/ui/steps/**: Modular UI steps for Streamlit.
- **src/utils/**: Utilities for logging, content safety, and more.
- **src/workflow/**: Workflow and session management.
- **tests/**, **tests_e2e/**: Unit and end-to-end tests.
- **test_data/**: Sample files for testing.
- **.github/**: GitHub workflows and configuration.
