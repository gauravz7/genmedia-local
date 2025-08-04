# Veo AI Prompt Engineering and Video Generation UI (No Service Account)

This is a web-based application designed to streamline the process of prompt engineering and video generation using Google's Veo AI models through the Vertex AI platform. It provides a user-friendly interface for generating, refining, and managing video creation prompts, as well as generating videos from text or images. This version of the application uses your default Google Cloud credentials, so no service account is required.

## Features

### 1. Advanced Prompt Engineering
- **AI-Powered Prompt Generation:** Users can input a simple idea, and the application leverages the Gemini 2.5 Flash model to generate a detailed, structured JSON prompt optimized for the Veo model.
- **AI-Powered Refinement:** Existing prompts can be iteratively refined using natural language instructions (e.g., "make it more dramatic," "change the setting to a futuristic city").
- **Optional Image Context:** Users can optionally upload an image along with their text prompt to provide visual context to the prompt generation model, leading to more accurate and relevant results.

### 2. Text-to-Video Generation
- **Batch Processing:** Add multiple text prompts to a queue for video generation.
- **Parallel Execution:** Run the generation for all prompts in the queue simultaneously, with each request handled in a separate thread for efficiency.
- **Customizable Parameters:** For each batch, users can select the Veo model (3.0 Fast or 3.0 Standard), set a generation seed, choose the aspect ratio (16:9 or 9:16), and provide a negative prompt.

### 3. Image-to-Video Generation
- **Sequential Workflow:** The UI guides the user through a step-by-step process:
    1.  Upload an image.
    2.  Crop the image to the desired aspect ratio (16:9 or 9:16).
    3.  Add an animation prompt and other parameters.
- **Batch Processing & Parallel Execution:** Add multiple configured image-and-prompt combinations to a queue and run them all in parallel.
- **Customizable Parameters:** For each image, users can set the animation prompt, select the Veo model, specify a seed, choose the aspect ratio, and provide a negative prompt.

### 4. Generation History
- **Persistent History:** All generation tasks (both text-to-video and image-to-video) are saved to a local SQLite database.
- **Visual History:** The history tab displays a comprehensive record of each task, including the prompt, status, and the final generated video or error message. For image-to-video tasks, the initial uploaded image is also displayed for easy reference.

### 5. Usage Dashboard
- **Local Database Reporting:** The settings tab includes a usage dashboard that provides reports based on the local generation history.
- **Failure Analysis:** The report includes a breakdown of common failure reasons, helping users diagnose and troubleshoot issues.

## Getting Started: A Step-by-Step Guide

This guide will walk you through the entire process of setting up and running the application, from a fresh `git clone` to generating your first video.

### Prerequisites
- You have a Google Cloud account with billing enabled.
- You have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed on your local machine.

### Step 1: Set Up Your Google Cloud Project
1.  **Create or Select a Project:**
    - If you don't have a project, create one in the [Google Cloud Console](https://console.cloud.google.com/).
    - Note your **Project ID**.

2.  **Enable APIs:**
    Enable the following APIs for your project. You can do this from the "APIs & Services" dashboard in the console.
    - Vertex AI API
    - Cloud Storage API

3.  **Create a GCS Bucket:**
    - In the Cloud Console, navigate to Cloud Storage and create a new bucket.
    - Choose a unique name for your bucket and note it down.

### Step 2: Authenticate Your User Account
This version of the application uses your personal Google Cloud credentials.

1.  **Log in with gcloud:**
    Open your terminal and run the following command. This will open a browser window for you to log in to your Google account.
    ```bash
    gcloud auth login
    ```

2.  **Set Your Project:**
    Tell gcloud which project to use.
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

### Step 3: Clone and Configure the Application
1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure `app_noservice.py`:**
    Open the `app_noservice.py` file and set the following variables to your own values:
    - `PROJECT_ID`: Your Google Cloud Project ID.
    - `GCS_BUCKET_NAME`: The name of the GCS bucket you created.

### Step 4: Run the Application
You are now ready to run the application!
```bash
python app_noservice.py
```
Open your web browser and navigate to `http://127.0.0.1:8080`. You can also use the "Settings" tab in the UI to validate your configuration.

## Running the Application

To run the application locally, use the following command:
```bash
python app_noservice.py
```
The application will be available at `http://127.0.0.1:8080`.

## Usage Guide

### Prompt Generator Tab
1.  Enter your core idea or concept into the **User Prompt** text area.
2.  (Optional) Upload an image to provide visual context for the prompt.
3.  Review or modify the **System Instructions** if needed.
4.  Click **Generate Final Prompt**. The AI-generated JSON prompt will appear below.
5.  (Optional) Use the **Refine with AI** feature to make iterative changes.
6.  Click **Add to Video Generation Queue** to send the prompt to the "Video Generation" tab.

### Video Generation Tab
1.  Add prompts from the "Prompt Generator" tab or paste them directly.
2.  Select the desired **Video Model**, **Seed**, **Aspect Ratio**, and add an optional **Negative Prompt**. These settings will apply to all prompts in the queue.
3.  Click **Run Parallel Generation**. The status of each video will appear below.

### Image to Video Tab
1.  Click **Image File** to select an image from your computer.
2.  A cropping modal will appear. Adjust the crop to your desired framing and click **Crop and Add to Queue**.
3.  The cropped image will be previewed, and the form fields will be enabled.
4.  Enter an **Animation Prompt**, and adjust the **Aspect Ratio**, **Model**, **Seed**, and **Negative Prompt** as needed.
5.  Click **Add to Queue**. The configured image and prompt will appear in the queue on the right.
6.  Repeat to add more images to the queue.
7.  Click **Run Parallel Image Generation** to start the generation for all items in the queue.

### Prompt History Tab
- This tab displays a record of all past generation tasks.
- Click on any item to expand it and view the details, including the initial image (if applicable) and the final video or error message.
