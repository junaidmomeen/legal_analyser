# Legal Document Analyzer

This project is a web application that helps you understand complex legal documents. Upload a PDF or an image of a document, and the AI-powered tool will provide a simple summary, identify important clauses, and generate a downloadable report.

## Features

*   **AI-Powered Analysis:** Uses Large Language Models via OpenRouter to analyze and simplify legal text.
*   **Multi-Format Support:** Accepts both PDF and image files (`.png`, `.jpg`).
*   **OCR Integration:** Automatically extracts text from scanned documents and images using Tesseract.
*   **In-Depth Reports:** Generates detailed reports highlighting key clauses, potential risks, and summaries.
*   **Downloadable Content:** Allows you to download the analysis as a PDF or JSON file.

## Tech Stack

*   **Backend:** Python, FastAPI
*   **Frontend:** React, TypeScript, Vite
*   **AI/OCR:** OpenRouter, Tesseract
*   **Containerization:** Docker, Docker Compose

---

## Project Setup

You can run this project using Docker (recommended for ease of use) or by setting up the frontend and backend environments manually.

### Prerequisites

*   **Docker and Docker Compose:** Required for the Docker setup. [Install Docker](https://docs.docker.com/get-docker/).
*   **Node.js and npm:** Required for the manual frontend setup. [Install Node.js](https://nodejs.org/en/download/).
*   **Python:** Required for the manual backend setup. [Install Python](https://www.python.org/downloads/).
*   **OpenRouter API Key:** The backend requires an API key to communicate with the AI service.
    1.  Go to [OpenRouter.ai](https://openrouter.ai/keys) to get your free key.
    2.  You will need this key for both setup methods.

---

### Method 1: Running with Docker (Recommended)

This method builds and runs the entire application in isolated containers, handling all dependencies for you.

**Step 1: Create the Backend Environment File**

The backend needs API keys and configuration, which are managed using a `.env` file.

1.  Navigate to the `backend` directory.
2.  Copy the example environment file:
    ```bash
    cp backend/env.example backend/.env
    ```
3.  Open the new `backend/.env` file and add your OpenRouter API key:
    ```env
    # backend/.env

    # Required: OpenRouter API Key for AI analysis
    # Get your key from: https://openrouter.ai/keys
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    ```

**Step 2: Build and Run the Containers**

From the project's root directory, run the following command:

```bash
docker-compose up --build
```

*   `--build` tells Docker to build the images for the `frontend` and `backend` based on their respective `Dockerfiles`. This may take a few minutes on the first run.
*   `up` starts the services defined in `docker-compose.yml`.

**Step 3: Access the Application**

Once the containers are running, you can access the frontend at:
[http://localhost:3000](http://localhost:3000)

---

### Method 2: Manual Local Setup

This method requires you to set up and run the frontend and backend services separately in your local environment.

#### Part 1: Backend Setup

**Step 1: Install OCR Dependencies**

For the backend to process images, you need to install Tesseract OCR.

*   **Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install tesseract-ocr libmagic1`
*   **macOS:** `brew install tesseract libmagic`
*   **Windows:** Download the installer from the [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page and follow the installation instructions.

**Step 2: Set Up a Python Virtual Environment**

From the project root, create and activate a virtual environment to manage dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Linux/macOS)
source venv/bin/activate

# Activate it (Windows)
.\venv\Scripts\activate

**Step 3: Install Backend Dependencies**

```bash
pip install -r requirements.txt

```

**Step 4: Configure Environment Variables**

Just like in the Docker setup, create a `.env` file in the `backend` directory.

1.  Copy the example: `cp backend/env.example backend/.env`
2.  Add your `OPENROUTER_API_KEY` to `backend/.env`.

**Step 5: Run the Backend Server**

```bash
uvicorn main:app --reload

```

The backend API will now be running at [http://localhost:8000](http://localhost:8000).

#### Part 2: Frontend Setup

**Step 1: Install Frontend Dependencies**

In a **new terminal**, navigate to the `frontend` directory and install the required Node.js packages.

```bash
cd frontend
npm install
```

**Step 2: Run the Frontend Development Server**

```bash
npm run dev
```

**Step 3: Access the Application**

The frontend will be available at [http://localhost:5173](http://localhost:5173). It is configured to connect to the backend API running on port 8000.

---
