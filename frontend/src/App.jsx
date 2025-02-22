import React, { useState } from "react";
import axios from "axios";
import "./App.css"; 


function App() {
  const [jsonData, setJsonData] = useState(null);
  const [jsonFilename, setJsonFilename] = useState("");
  const [file, setFile] = useState(null);
  const [showNext, setShowNext] = useState(false);
  const [scanOutput, setScanOutput] = useState("");
  const [filePath, setFilePath] = useState("");
  const [pulsateNext, setPulsateNext] = useState(false);


  // Handler for BOM file selection
  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  // Upload BOM file to backend
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
      setJsonFilename(response.data.filename);
      setFile(null);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to upload file. Please try again.");
    }
  };

  // Download generated JSON file
  const handleDownload = async () => {
    if (!jsonFilename) {
      alert("No JSON file available for download.");
      return;
    }
    try {
      const response = await axios.get(`http://127.0.0.1:8000/download/${jsonFilename}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = jsonFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => {
        setPulsateNext(true); // ✅ Delay ripple effect slightly
      }, 500);
    } catch (error) {
      alert("Failed to download JSON file.");
    }
  };  

  // Show the next section (model scan options)
  const handleNext = () => {
    setShowNext(true);
    setPulsateNext(false); // ✅ Stop ripple effect
  };  

  const handlePrevious = () => {
    setShowNext(false);
  };  
  

  // Handler for file path input change
  const handleFilePathChange = (event) => {
    let inputPath = event.target.value;
    // Remove surrounding quotes if present
    if (inputPath.startsWith("\"") && inputPath.endsWith("\"")) {
      inputPath = inputPath.slice(1, -1);
    }
    setFilePath(inputPath);
  };
  

  // Call the backend to perform auto-scan by file path
  const handleAutoScan = async () => {
    if (!filePath) {
      alert("Please enter a file path.");
      return;
    }
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/scan-model-path",
        { file_path: filePath }
      );
      setScanOutput(response.data.scanOutput);
      setFilePath("");
    } catch (error) {
      console.error("Error scanning model file:", error);
      alert("Failed to scan model file. Please try again.");
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>AI Model BOM Generator</h1>
      {!showNext && (
        <div style={styles.content}>
          {/* Upload BOM File Section */}
          <div style={styles.panel}>
            <h2 style={styles.header}>📂 Upload BOM File</h2>
            <input
              type="file"
              onChange={handleFileChange}
              style={styles.input}
            />
            <button onClick={handleUpload} style={styles.button}>
              Upload
            </button>
          </div>
          {/* JSON Output Section */}
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
          {/* Download JSON & NEXT Button Section */}
          <div style={styles.panel}>
            <h2 style={styles.header}>⬇️ Download JSON</h2>
            <button
              onClick={handleDownload}
              style={{ ...styles.button, opacity: jsonFilename ? 1 : 0.5 }}
              disabled={!jsonFilename}
            >
              Download JSON
            </button>
            <br></br>
            <div className={`next-button-container ${pulsateNext ? "pulsatingButton" : ""}`}>
              <button onClick={handleNext} className="button">
                NEXT
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Model Scan Options Section */}
      {showNext && (
        <div style={styles.nextContainer}>
          <div style={styles.scanSection}>
            <h3 style={styles.subHeader}>Auto Scan by File Path</h3>
            <input
              type="text"
              value={filePath}
              onChange={handleFilePathChange}
              style={styles.input}
              placeholder="e.g., C:\Users\Username\model.pkl"
            />
            <button onClick={handleAutoScan} style={styles.button}>
              Auto Scan
            </button>
          </div>
          <div style={styles.scanOutput}>
            <h3 style={styles.header}>Model Scan Output</h3>
            <pre>{scanOutput || "No scan output available"}</pre>
          </div>
          <button onClick={handlePrevious} style={{ ...styles.button, width: "15%" }}>Previous</button>
        </div>
      )}
    </div>
  );
}

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
    height: "calc(100vh - 60px)",
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
    width: "80%",
  },
  header: {
    fontSize: "22px",
    fontWeight: "bold",
    marginBottom: "10px",
  },
  subHeader: {
    fontSize: "18px",
    marginBottom: "8px",
  },
  nextContainer: {
    marginTop: "20px",
    padding: "20px",
    textAlign: "center",
  },
  scanSection: {
    marginBottom: "20px",
  },
  scanOutput: {
    marginTop: "20px",
    backgroundColor: "#333",
    color: "#fff",
    padding: "20px",
    fontFamily: "monospace",
    fontSize: "14px",
    borderRadius: "8px",
    maxHeight: "50vh",
    overflowY: "auto",
    width: "80%",
    margin: "0 auto",
    boxShadow: "inset 0px 0px 10px #00FF00",
  },
  pulsatingButton: {
    animation: "pulse 1.5s infinite",
  },
};

export default App;
