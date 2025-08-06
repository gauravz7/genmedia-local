# GenMedia Garage

A web-based application for prompt engineering, video generation, and creative AI tooling using Google's Generative AI models via Vertex AI.

## Features

- **Prompt Engineering:** A dedicated interface for crafting and refining detailed prompts for generative models.
- **Video Generation:**
    - **Text-to-Video:** Generate videos from text prompts using Veo models.
    - **Image-to-Video:** Animate still images with text prompts.
    - **VEO Edit & Veo2 Controls:** Advanced video editing and inpainting/outpainting capabilities.
- **Image Generation & Editing:**
    - **Imagen3 Editing:** Advanced image editing with inpainting, outpainting, and mask-free editing.
    - **Virtual Try-On (VTO):** Place apparel on models.
    - **Product Recontextualization:** Change the background of product images.
    - **Segmentation:** Isolate subjects from the background.
- **Centralized History:** All generation tasks are saved to a local SQLite database for review.
- **Settings & Usage:** Configure your GCP settings and view usage reports based on local history.
- **Modular & Scalable:** The application is broken into logical modules for easy extension.
- **Light & Dark Mode:** Toggle between themes for your comfort.

## Project Structure

The application is organized into the following modules:

-   `app.py`: The main entry point for the Flask application. It creates the app instance, initializes extensions, and registers routes.
-   `config.py`: Contains the application's configuration settings, such as project IDs and database URIs.
-   `models.py`: Defines the SQLAlchemy database models (`GenerationHistory` and `SystemInstruction`).
-   `database.py`: Contains the `init_db` function to create the database tables.
-   `extensions.py`: Initializes the `SQLAlchemy` extension to avoid circular dependencies.
-   `utils.py`: A collection of helper functions for tasks like GCS uploads, prompt generation, and video processing.
-   `services.py`: Contains the core business logic for each of the application's services.
-   `routes.py`: Defines all the Flask routes and maps them to the appropriate service functions.
-   `static/`: Contains the CSS and JavaScript files for the frontend.
-   `templates/`: Contains the `index.html` file, which serves as the main UI for the application.

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
python app.py
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
pkill -f app.py
```
Then, restart the application using `./start_local.sh`.
