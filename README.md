# GenMedia Garage

A web-based application for prompt engineering, video generation, and creative AI tooling using Google's Generative AI models via Vertex AI.

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

### 3. Run the Application

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

## Cloud Deployment (Cloud Run)

This application can be deployed as a serverless container on Google Cloud Run.

### 1. Enable APIs
Ensure you have the following APIs enabled in your Google Cloud project:
- Vertex AI API
- Cloud Build API
- Artifact Registry API
- Cloud Run API

### 2. Set Permissions
The Cloud Build service account needs permissions to deploy to Cloud Run and act as an IAM user. Run the following commands, replacing `PROJECT_ID` with your project ID:
```bash
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 3. Deploy
Submit the build and deployment job to Cloud Build:
```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_PROJECT_ID=your-gcp-project-id,_GCS_BUCKET_NAME=your-gcs-bucket-name
```
Replace `your-gcp-project-id` and `your-gcs-bucket-name` with your actual project ID and GCS bucket name.

The command will output the URL of your deployed service.

### Troubleshooting

**"Port 8080 is already in use"**

This error means another process is using the port. This can happen if a previous instance of the application did not shut down correctly. To fix this, you can run the cleanup command from the `start_local.sh` script manually, or simply run the script again, as it is designed to handle this situation.

To manually kill the process:
```bash
pkill -f app_noservice.py
```
Then, restart the application using `./start_local.sh`.
