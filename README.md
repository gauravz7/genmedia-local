# Veo AI Prompt Engineering and Video Generation UI

A web-based application for prompt engineering and video generation using Google's Veo AI models via Vertex AI.

## Features

- **AI-Powered Prompt Generation & Refinement:** Use the Gemini 2.5 Flash model to generate and refine detailed JSON prompts for Veo.
- **Text-to-Video & Image-to-Video:** Generate videos from text prompts or images with customizable parameters.
- **Batch Processing:** Queue multiple jobs to run in parallel.
- **Persistent History:** All tasks are saved to a local SQLite database for review.
- **Usage Dashboard:** View reports based on your local generation history.

## Local Setup and Usage

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) is installed.
- You have a Google Cloud project with the **Vertex AI** and **Cloud Storage** APIs enabled.
- You have a GCS bucket for storing image assets.

### 1. Configure Authentication

This application uses your local Google Cloud user credentials.

1.  **Log in with your Google Account:**
    ```bash
    gcloud auth application-default login
    ```
    This will open a browser window for you to log in and grant permissions.

2.  **Set your project:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Application
Open `app_noservice.py` and update the following variables with your project details:
- `PROJECT_ID`
- `GCS_BUCKET_NAME`

### 4. Run the Application

**As a background service on macOS:**

1.  **Make the script executable:**
    ```bash
    chmod +x start_local.sh
    ```
2.  **Start the service:**
    ```bash
    ./start_local.sh
    ```
The application will be available at `http://localhost:8080`.

**To stop the service:**

The `start_local.sh` script will tell you the exact command to run to stop the specific service instance it created. Look for the `To stop the service, run:` message in the script's output.

**For direct terminal execution:**
```bash
python app_noservice.py
```

### Troubleshooting

**"Port 8080 is already in use"**

This error means another process is using the port. This can happen if a previous instance of the application did not shut down correctly. To fix this, you can run the cleanup command from the `start_local.sh` script manually, or simply run the script again, as it is designed to handle this situation.

To manually kill the process:
```bash
pkill -f app_noservice.py
```
Then, restart the application using `./start_local.sh`.
