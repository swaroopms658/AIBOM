import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [jsonData, setJsonData] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      console.log("Uploading file:", file.name);
      const response = await axios.post(
        "http://127.0.0.1:8000/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      console.log("Server response:", response.data);
      setJsonData(response.data);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("File processing failed. Check console for details.");
    }
  };

  const handleDownload = () => {
    if (!jsonData) return;

    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "libraries.json";
    link.click();
  };

  return (
    <div style={{ textAlign: "center", padding: "50px" }}>
      <h1>AI BOM Frontend</h1>
      <input type="file" onChange={handleFileChange} accept=".py" />
      <button onClick={handleUpload} style={{ marginLeft: "10px" }}>
        Upload
      </button>

      {jsonData && (
        <div style={{ marginTop: "20px", textAlign: "left" }}>
          <h3>Extracted Libraries:</h3>
          <pre>{JSON.stringify(jsonData, null, 2)}</pre>
          <button onClick={handleDownload}>Download JSON</button>
        </div>
      )}
    </div>
  );
}

export default App;
