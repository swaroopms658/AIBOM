# AI BOM Framework

AI BOM Framework

This project provides a comprehensive framework for generating Bill of Materials (BOM) for AI projects. It includes:

FastAPI Backend:
Processes file uploads and extracts dependencies to generate BOMs in CycloneDX format.
React Frontend:
Allows users to easily upload files and download the generated BOMs.
Security Vulnerability Scans:
Integrated with the modelscan tool to perform security vulnerability scans on AI models, ensuring that potential risks (such as unsafe operations) are detected and reported.

## Features

- **FastAPI Backend**: Handles file uploads, processes files to extract dependencies, and generates BOMs in CycloneDX format.
- **React Frontend**: Allows users to upload files and download the generated BOMs.
- **CORS Enabled**: Allows frontend and backend to communicate seamlessly.
- **Static File Serving**: Serves generated BOMs from a static directory.

---

## Backend Setup

### Prerequisites

- Python 3.8+
- FastAPI
- Uvicorn
- Requests
- Psutil

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/swaroopms658/AIBOM.git
   cd AIBOM/backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows (Command Prompt)
   venv\Scripts\Activate.ps1 # On Windows (PowerShell)
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
5. Change the download path for the directory at the backend:
UPLOAD_DIR = r"C:\Users\Username\Downloads\upload"
EXTRACT_DIR = r"C:\Users\Username\Downloads\extracted"
---
6.Create two different terminals in code editor one for frontend and one for backend

## API Endpoints

- **POST /upload**: Upload a file and generate a BOM.
- **GET /download/{filename}**: Download a generated BOM file.
- **POST /scan-model-path**: Scan an AI model file by file path.

---

## Frontend Setup

### Prerequisites

- Node.js
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Run the frontend:
   ```bash
   npm start
   # or
   yarn start
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

---

## Project Structure

```md
AIBOM/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── ...
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── ...
│   ├── public/
│   ├── package.json
│   ├── ...
└── README.md
```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

## License

This project is licensed under the [MIT License](LICENSE).
