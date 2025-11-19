// frontend/src/pages/Upload.jsx
import React, { useState, useEffect, useRef } from "react";
import FileUpload from "../components/FileUpload";
import { apiGet } from "../api";

const POLL_INTERVAL_ACTIVE = 2000;

function normalizeStatusPayload(payload = {}) {
  const status = payload.status ?? payload.state ?? payload.upload_status ?? "unknown";
  const processed =
    payload.processed ?? payload.processed_count ?? payload.processedEmails ?? 0;
  const total =
    payload.total ?? payload.total_count ?? payload.totalEmails ?? 0;
  const chunks =
    payload.chunks ?? payload.total_chunks ?? payload.chunk_count ?? 0;
  const percent =
    total && total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0;
  return { status, processed, total, chunks, percent, raw: payload };
}

export default function Upload() {
  const [uploadId, setUploadId] = useState(null);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [format, setFormat] = useState("csv");
  const pollingRef = useRef(null);

  async function fetchOnce(id) {
    if (!id) return null;
    try {
      setError(null);
      const payload = await apiGet(`/uploads/${id}`);
      const normalized = normalizeStatusPayload(payload);
      setProgress(normalized);
      return normalized;
    } catch (err) {
      console.error("fetchOnce error", err);
      setError("Failed to fetch upload status");
      return null;
    }
  }

  useEffect(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    if (!uploadId) {
      setProgress(null);
      return;
    }

    (async () => {
      await fetchOnce(uploadId);
    })();

    pollingRef.current = setInterval(async () => {
      const res = await fetchOnce(uploadId);
      if (!res) return;
      const s = String(res.status).toLowerCase();
      if (["completed", "cancelled", "failed", "done"].includes(s) || res.percent >= 100) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }, POLL_INTERVAL_ACTIVE);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      pollingRef.current = null;
    };
  }, [uploadId]);

  const onUploaded = (id, meta) => {
    setUploadId(id);
    setError(null);
    setProgress({
      status: "queued",
      processed: 0,
      total: meta?.total ?? 0,
      chunks: meta?.chunks ?? 0,
      percent: 0,
    });
  };

  const downloadResults = async (selectedFormat = "csv") => {
    try {
      const url = `${import.meta.env.VITE_API_URL}/results/download/${uploadId}?file_format=${selectedFormat}`;
      const res = await fetch(url);
      if (!res.ok) {
        console.error("Download failed", res.status);
        setError("Download failed");
        return;
      }
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `results_${uploadId}.${selectedFormat}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error("Download error:", err);
      setError("Download error");
    }
  };

  const isCompleted =
    progress &&
    (progress.percent >= 100 || ["completed", "done"].includes(String(progress.status).toLowerCase()));

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Upload Email List</h2>

      <FileUpload onUploaded={onUploaded} />

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-800 rounded">
          {error}
        </div>
      )}

      {uploadId && progress && (
        <div className="mt-6 bg-white p-5 rounded shadow max-w-xl">
          <h3 className="text-lg font-semibold mb-2">Progress</h3>

          <p className="mb-2">
            <strong>Upload ID:</strong> <code>{uploadId}</code>
          </p>

          <div className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <div>
                <strong>Status:</strong> {progress.status}
              </div>
              <div>{progress.percent}%</div>
            </div>

            <div className="w-full bg-gray-200 rounded h-3 overflow-hidden">
              <div
                className="h-3 rounded bg-green-500"
                style={{ width: `${progress.percent}%`, transition: "width 400ms ease" }}
                aria-hidden
              />
            </div>
          </div>

          <p><strong>Processed:</strong> {progress.processed}</p>
          <p><strong>Total:</strong> {progress.total}</p>
          <p><strong>Chunks:</strong> {progress.chunks}</p>

          {isCompleted && (
            <div className="mt-4">
              <p className="text-green-700 mb-3">Upload processing completed.</p>

              <div className="flex items-center gap-3 mt-2">
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="border px-3 py-2 rounded"
                >
                  <option value="csv">CSV (.csv)</option>
                  <option value="txt">TXT (.txt)</option>
                </select>

                <button
                  onClick={() => downloadResults(format)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                  Download Results
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!uploadId && <div className="mt-6 text-sm text-gray-600">No upload in progress.</div>}
    </div>
  );
}
