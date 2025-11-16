// frontend/src/components/FileUpload.jsx

import React, { useState } from "react";
import { apiPost } from "../api";

export default function FileUpload({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError("");
  };

  const uploadFile = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await apiPost("/uploads/create", formData);
      setUploadStatus(data);

      if (onUploaded) onUploaded(data.upload_id);

    } catch (err) {
      setError("Upload failed!");
    }
  };

  return (
    <div className="w-full max-w-xl p-8 bg-white shadow rounded">
      <input
        type="file"
        accept=".csv, .xlsx, .xls"
        onChange={handleFileChange}
        className="mb-3"
      />

      {file && (
        <p className="text-green-700 mb-3">
          Selected: <strong>{file.name}</strong>
        </p>
      )}

      <button
        onClick={uploadFile}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Upload File
      </button>

      {error && <p className="mt-3 text-red-600">{error}</p>}

      {uploadStatus && (
        <div className="mt-5 text-sm bg-gray-100 p-3 rounded">
          <p>Upload ID: {uploadStatus.upload_id}</p>
          <p>Total Emails: {uploadStatus.total}</p>
          <p>Chunks: {uploadStatus.chunks}</p>
        </div>
      )}
    </div>
  );
}
