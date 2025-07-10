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

## Environment Variables

VoiceMate requires several environment variables for cloud services and integrations. Create a `.env` file in the project root with the following content (replace values with your own secrets):

```env
AZURE_KEYVAULT_URL=https://keyvoicemate.vault.azure.net/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://voicemate-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MODEL=gpt-4
API_VERSION=2024-12-01-preview

AZURE_SPEECH_API_KEY=your-azure-speech-api-key
AZURE_SPEECH_REGION=swedencentral
ELEVENLABS_API_KEY=your-elevenlabs-api-key

APPINSIGHTS_CONNECTION_STRING=your-appinsights-connection-string

AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string

CONTENT_SAFETY_ENDPOINT=https://contentsafevoicemate.cognitiveservices.azure.com/
CONTENT_SAFETY_KEY=your-content-safety-key

ELEVENLABS_PASSWORD=your-elevenlabs-password
```

### Variable Descriptions
- **AZURE_KEYVAULT_URL**: Azure Key Vault endpoint for secrets management.
- **AZURE_OPENAI_API_KEY**: API key for Azure OpenAI service.
- **AZURE_OPENAI_ENDPOINT**: Endpoint for Azure OpenAI API.
- **AZURE_OPENAI_DEPLOYMENT**: Name of the OpenAI deployment (e.g., gpt-4o).
- **AZURE_OPENAI_MODEL**: Model name for OpenAI (e.g., gpt-4).
- **API_VERSION**: API version for Azure OpenAI.
- **AZURE_SPEECH_API_KEY**: API key for Azure Speech service.
- **AZURE_SPEECH_REGION**: Azure region for Speech service.
- **ELEVENLABS_API_KEY**: API key for ElevenLabs TTS.
- **APPINSIGHTS_CONNECTION_STRING**: Azure Application Insights connection string for monitoring/logging.
- **AZURE_STORAGE_CONNECTION_STRING**: Azure Blob Storage connection string for logs and data.
- **CONTENT_SAFETY_ENDPOINT**: Endpoint for Azure Content Safety API.
- **CONTENT_SAFETY_KEY**: API key for Content Safety.
- **ELEVENLABS_PASSWORD**: Password for ElevenLabs (if required).

> **Important:** All URLs and keys in the example below must be replaced with your own values from your Azure (or other cloud) account. The provided links are only examples!

> **Note:** Never commit your `.env` file or secrets to version control.

## How to Run VoiceMate

### 1. Prerequisites

- Python 3.10 or newer
- [pip](https://pip.pypa.io/en/stable/)
- (Optional) Docker

### 2. Clone the Repository

```bash
git clone <repository_url>
cd VoiceMate
```

### 3. Configure Environment Variables

Create a `.env` file in the project root using the template below (fill in with your own credentials):

```env
AZURE_KEYVAULT_URL=https://keyvoicemate.vault.azure.net/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://voicemate-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MODEL=gpt-4
API_VERSION=2024-12-01-preview

AZURE_SPEECH_API_KEY=your-azure-speech-api-key
AZURE_SPEECH_REGION=swedencentral
ELEVENLABS_API_KEY=your-elevenlabs-api-key

APPINSIGHTS_CONNECTION_STRING=your-appinsights-connection-string

AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string

CONTENT_SAFETY_ENDPOINT=https://contentsafevoicemate.cognitiveservices.azure.com/
CONTENT_SAFETY_KEY=your-content-safety-key

ELEVENLABS_PASSWORD=your-elevenlabs-password
```

**Note:** The `.env` file is git-ignored (`.gitignore`). Never share it publicly!

### 4. Install Dependencies (Locally)

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

Install the required libraries:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will be available at: [http://localhost:8501](http://localhost:8501)

---

## Running with Docker

1. Build the Docker image:

   ```bash
   docker build -t voicemate .
   ```

2. Run the container (make sure you have the `.env` file in your project directory):

   ```bash
   docker run -p 8501:80 --env-file .env voicemate-app:latest
   ```

The app will be available at: [http://localhost:80](http://localhost:80)

---

## Testing

To run unit tests:

```bash
pytest
```

---

## Additional Information

- All session logs are automatically uploaded to Azure Blob Storage.
- The app supports PDF files, images, tables, and audio generation via Azure TTS and ElevenLabs.
- The UI is built with Streamlit.
