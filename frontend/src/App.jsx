import React, { useState } from "react";
import axios from "axios";

function App() {
  const [jsonData, setJsonData] = useState(null);
  const [jsonFilename, setJsonFilename] = useState("");
  const [file, setFile] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/upload",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setJsonData(response.data.data);
      setJsonFilename(response.data.json_file || "downloaded.json");
      setFile(null);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to upload file. Please try again.");
    }
  };

  const handleDownload = async () => {
    if (!jsonFilename) {
      alert("No JSON file available for download.");
      return;
    }

    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/static/${jsonFilename}`,
        { responseType: "blob" }
      );

      const blob = new Blob([response.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = jsonFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("Failed to download JSON file.");
    }
  };

  return (
    <div style={styles.container}>
      {/* Left Panel - Upload File */}
      <div style={styles.panel}>
        <h2 style={styles.header}>📂 Upload File</h2>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} style={styles.button}>
          Upload
        </button>
      </div>

      {/* Center Panel - JSON Output */}
      <div style={styles.centerPanel}>
        <h2 style={styles.header}>📜 JSON Output</h2>
        <pre style={styles.jsonBox}>
          {jsonData ? JSON.stringify(jsonData, null, 2) : "No JSON available"}
        </pre>
      </div>

      {/* Right Panel - Download JSON */}
      <div style={styles.panel}>
        <h2 style={styles.header}>⬇️ Download JSON</h2>
        <button
          onClick={handleDownload}
          style={styles.button}
          disabled={!jsonFilename}
        >
          Download JSON
        </button>
      </div>
    </div>
  );
}

// CSS styles
const styles = {
  container: {
    display: "flex",
    width: "100vw",
    height: "100vh",
    fontFamily: "Arial, sans-serif",
  },
  panel: {
    flex: 1,
    padding: "20px",
    textAlign: "center",
    backgroundColor: "black",
    borderRight: "2px solid #ccc",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
  centerPanel: {
    flex: 2,
    padding: "20px",
    textAlign: "center",
    backgroundColor: "#007BFF",
    borderRight: "2px solid #ccc",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
  button: {
    marginTop: "15px",
    backgroundColor: "#007BFF",
    color: "#fff",
    padding: "12px 20px",
    border: "none",
    cursor: "pointer",
    borderRadius: "8px",
    fontSize: "16px",
    width: "80%",
  },
  jsonBox: {
    textAlign: "left",
    backgroundColor: "#222",
    color: "#00ff00",
    padding: "20px",
    fontFamily: "Courier New",
    fontSize: "16px",
    borderRadius: "8px",
    maxHeight: "75vh",
    overflowY: "auto",
    flexGrow: 1,
    width: "90%",
  },
  header: {
    fontSize: "22px",
    fontWeight: "bold",
    marginBottom: "10px",
  },
};

export default App;
