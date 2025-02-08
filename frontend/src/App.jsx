import { useState } from "react";
import axios from "axios";
import FileSaver from "file-saver";

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [jsonFile, setJsonFile] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResponse(res.data.data);
      setJsonFile(res.data.json_file);
    } catch (error) {
      console.error("Upload error:", error);
      setResponse({ error: "Failed to process file" });
    }
  };

  const handleDownload = async () => {
    if (jsonFile) {
      try {
        const res = await axios.get(
          `http://127.0.0.1:8000/static/${jsonFile}`,
          {
            responseType: "blob",
          }
        );
        FileSaver.saveAs(res.data, jsonFile);
      } catch (error) {
        console.error("Download error:", error);
      }
    }
  };

  return (
    <div style={{ textAlign: "center", padding: "50px" }}>
      <h1>AI BOM Frontend</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "10px" }}>
        Upload
      </button>

      {response && (
        <div style={{ marginTop: "20px", textAlign: "left" }}>
          <h3>Extracted Dependencies:</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
          <button onClick={handleDownload} style={{ marginTop: "10px" }}>
            Download JSON
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
