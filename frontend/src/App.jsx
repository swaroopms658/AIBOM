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
      {/* Title */}
      <h1 style={styles.title}>AI Model BOM Generator</h1>

      <div style={styles.content}>
        {/* Left Panel - Upload File */}
        <div style={styles.panel}>
          <h2 style={styles.header}>📂 Upload File</h2>
          <input type="file" onChange={handleFileChange} style={styles.input} />
          <button onClick={handleUpload} style={styles.button}>
            Upload
          </button>
        </div>

        {/* Center Panel - JSON Output */}
        <div style={styles.centerPanel}>
          <h2 style={styles.header}>📜 JSON Output</h2>
          <div style={styles.jsonBox}>
            <pre>
              {jsonData
                ? JSON.stringify(jsonData, null, 2)
                : "No JSON available"}
            </pre>
          </div>
        </div>

        {/* Right Panel - Download JSON */}
        <div style={styles.panel}>
          <h2 style={styles.header}>⬇️ Download JSON</h2>
          <button
            onClick={handleDownload}
            style={{ ...styles.button, opacity: jsonFilename ? 1 : 0.5 }}
            disabled={!jsonFilename}
          >
            Download JSON
          </button>
        </div>
      </div>
    </div>
  );
}

// CSS styles
const styles = {
  container: {
    width: "100vw",
    height: "100vh",
    fontFamily: "'Inter', sans-serif",
    backgroundColor: "#F5F5F5",
    color: "#333",
    overflow: "hidden",
    textAlign: "center",
  },
  title: {
    fontSize: "28px",
    fontWeight: "bold",
    padding: "20px",
    backgroundColor: "#007BFF",
    color: "#fff",
    margin: "0",
  },
  content: {
    display: "flex",
    height: "calc(100vh - 60px)", // Adjusting height after title
  },
  panel: {
    flex: 1,
    padding: "20px",
    textAlign: "center",
    backgroundColor: "#FFFFFF",
    borderRight: "1px solid #DDD",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    boxShadow: "0 0 10px rgba(0, 0, 0, 0.1)",
  },
  centerPanel: {
    flex: 2,
    padding: "20px",
    textAlign: "center",
    backgroundColor: "#FFFFFF",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    boxShadow: "0 0 10px rgba(0, 0, 0, 0.1)",
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
    transition: "all 0.3s",
  },
  jsonBox: {
    textAlign: "left",
    backgroundColor: "#222",
    color: "#00FF00",
    padding: "20px",
    fontFamily: "monospace",
    fontSize: "14px",
    borderRadius: "8px",
    maxHeight: "70vh",
    overflowY: "auto",
    flexGrow: 1,
    width: "90%",
    boxShadow: "inset 0px 0px 10px #00FF00",
  },
  input: {
    backgroundColor: "#FFF",
    color: "#333",
    padding: "10px",
    borderRadius: "5px",
    border: "1px solid #CCC",
    marginTop: "10px",
  },
  header: {
    fontSize: "22px",
    fontWeight: "bold",
    marginBottom: "10px",
  },
};

export default App;
