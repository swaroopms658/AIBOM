# AI BOM Framework

This project provides a framework for generating Bill of Materials (BOM) for AI projects. It includes a FastAPI backend for processing files and generating BOMs in CycloneDX format, and a React frontend for uploading files and downloading the generated BOMs.

## Features

- **FastAPI Backend**: Handles file uploads, processes files to extract dependencies, and generates BOMs in CycloneDX format.
- **React Frontend**: Allows users to upload files and download the generated BOMs.
- **CORS Enabled**: Allows frontend and backend to communicate seamlessly.
- **Static File Serving**: Serves generated BOMs from a static directory.

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
   git clone https://github.com/yourusername/ai-bom-framework.git
   cd ai-bom-framework/backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### API Endpoints

- **POST /upload**: Upload a file and generate a BOM.
- **GET /download/{filename}**: Download a generated BOM file.

## Frontend Setup

### Prerequisites

- Node.js
- npm or yarn

### Installation

1. Navigate to the frontend directory:

   ```bash
   cd ../frontend
   ```

2. Install the dependencies:

   ```bash
   npm install
   # or
   yarn install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

### Usage

1. Open your browser and navigate to `http://localhost:3000`.
2. Use the upload button to upload a file.
3. Once the file is processed, use the download button to download the generated BOM.

## Project Structure

ai-bom-framework/ ├── backend/ │ ├── main.py │ ├── requirements.txt │ └── ... ├── frontend/ │ ├── src/ │ │ ├── App.jsx │ │ └── ... │ ├── public/ │ ├── package.json │ └── ... └── README.md

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
