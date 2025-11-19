// frontend/src/pages/Results.jsx
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { DOWNLOAD_RESULTS_API, UPLOAD_STATUS_API } from "../api";

export default function Results() {
  const { id } = useParams();

  const [status, setStatus] = useState("loading");
  const [total, setTotal] = useState(0);
  const [processed, setProcessed] = useState(0);
  const [results, setResults] = useState([]);
  const [format, setFormat] = useState("csv");

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${UPLOAD_STATUS_API}/${id}`);
        if (!res.ok) {
          console.error("Failed to fetch status", res.status);
          setStatus("unknown");
          return;
        }
        const data = await res.json();
        setStatus(data.status || "unknown");
        setTotal(data.total || 0);
        setProcessed(data.processed || 0);
      } catch (err) {
        console.error("Error fetching status:", err);
        setStatus("unknown");
      }
    };

    fetchStatus();
  }, [id]);

  const handleDownload = async () => {
    const url = `${DOWNLOAD_RESULTS_API}/${id}?file_format=${format}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        alert("Failed to download file");
        return;
      }
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `results_${id}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Download error:", error);
      alert("Failed to download file");
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">
        Results for Upload ID: <span className="text-blue-600">{id}</span>
      </h2>

      <div className="border rounded-lg p-4 bg-white shadow mb-6">
        <p className="text-lg mb-1">
          <strong>Status:</strong>{" "}
          <span className={status === "completed" ? "text-green-600" : "text-blue-600"}>
            {status}
          </span>
        </p>

        <p><strong>Processed:</strong> {processed}</p>
        <p><strong>Total:</strong> {total}</p>

        {status === "completed" && (
          <p className="text-green-600 font-semibold mt-2">Processing completed.</p>
        )}
      </div>

      {status === "completed" && (
        <div className="border rounded-lg p-4 bg-white shadow mb-6">
          <h3 className="text-xl font-semibold mb-3">Download Results</h3>

          <div className="flex items-center gap-3">
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="px-3 py-2 border rounded-md bg-white"
            >
              <option value="csv">CSV (.csv)</option>
              <option value="txt">Text (.txt)</option>
            </select>

            <button
              onClick={handleDownload}
              className="px-5 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
