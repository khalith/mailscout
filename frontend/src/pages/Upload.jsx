// frontend/src/pages/Upload.jsx
import React, { useState, useEffect, useRef } from "react";
import FileUpload from "../components/FileUpload";
import { apiGet } from "../api";

/**
 * Robust Upload page
 * - polls backend for status
 * - tolerant to varied response keys (processed vs processed_count, total vs total_count)
 * - stops polling when finished
 */

const POLL_INTERVAL_ACTIVE = 2000; // ms when upload is active
const POLL_INTERVAL_IDLE = 5000;   // ms when no uploadId or finished

function normalizeStatusPayload(payload = {}) {
  // Accept multiple possible shapes from backend (defensive)
  const status = payload.status ?? payload.state ?? payload.upload_status ?? "unknown";

  const processed = 
    // common keys
    payload.processed ??
    payload.processed_count ??
    // older UI shape
    payload.processedEmails ??
    0;

  const total =
    payload.total ??
    payload.total_count ??
    payload.totalEmails ??
    0;

  const chunks =
    payload.chunks ??
    payload.total_chunks ??
    payload.chunk_count ??
    0;

  // compute percent defensively
  const percent =
    total && total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0;

  // pass through anything else user may want
  return { status, processed, total, chunks, percent, raw: payload };
}

export default function Upload() {
  const [uploadId, setUploadId] = useState(null);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const pollingRef = useRef(null);

  // Fetch once immediately whenever uploadId is set or on manual refresh
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

  // Start/stop polling whenever uploadId changes or progress changes to finished.
  useEffect(() => {
    // clear any existing poll
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    if (!uploadId) {
      setProgress(null);
      return;
    }

    let active = true;

    // immediate fetch
    (async () => {
      const res = await fetchOnce(uploadId);
      // if finished immediately, skip polling
      if (!res) return;
      if (["completed", "cancelled", "failed", "done"].includes(String(res.status).toLowerCase()) || res.percent >= 100) {
        active = false;
        return;
      }
    })();

    // else poll regularly
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetchOnce(uploadId);
        if (!res) return;

        const s = String(res.status).toLowerCase();
        if (["completed", "cancelled", "failed", "done"].includes(s) || res.percent >= 100) {
          // reached terminal state -> stop polling
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      } catch (err) {
        // keep polling but show error
        console.error("poll error", err);
        setError("Error polling status (see console)");
      }
    }, POLL_INTERVAL_ACTIVE);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      active = false;
    };
  }, [uploadId]);

  const onUploaded = (id, meta) => {
    // FileUpload component should call onUploaded(id) on success.
    setUploadId(id);
    // clear any prior errors/progress
    setError(null);
    setProgress({ status: "queued", processed: 0, total: meta?.total ?? 0, chunks: meta?.chunks ?? 0, percent: 0 });
  };

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

          <p className="mb-2"><strong>Upload ID:</strong> <code>{uploadId}</code></p>

          <div className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <div><strong>Status:</strong> {progress.status}</div>
              <div>{progress.percent}%</div>
            </div>

            <div className="w-full bg-gray-200 rounded h-3 overflow-hidden">
              <div
                className="h-3 rounded"
                style={{ width: `${progress.percent}%`, transition: "width 400ms ease" }}
                aria-hidden
              />
            </div>
          </div>

          <p><strong>Processed:</strong> {progress.processed}</p>
          <p><strong>Total:</strong> {progress.total}</p>
          <p><strong>Chunks:</strong> {progress.chunks}</p>

          {progress.percent >= 100 && <p className="mt-2 text-green-700">Upload processing completed.</p>}
        </div>
      )}

      {!uploadId && (
        <div className="mt-6 text-sm text-gray-600">No upload in progress.</div>
      )}
    </div>
  );
}
