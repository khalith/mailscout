// frontend/src/components/ProgressTracker.jsx
import { useEffect, useState } from "react";
import { getUploadStatus } from "../api";

export default function ProgressTracker({ uploadId }) {
  const [data, setData] = useState({
    status: "queued",
    processed: 0,
    total: 0,
    chunks: 0,
  });

  useEffect(() => {
    if (!uploadId) return;

    const interval = setInterval(async () => {
      try {
        const json = await getUploadStatus(uploadId);

        setData({
          status: json.status ?? "queued",
          processed: json.processed_count ?? 0,
          total: json.total_count ?? 0,
          chunks: json.chunks ?? 0,
        });
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [uploadId]);

  const percentage =
    data.total > 0 ? Math.round((data.processed / data.total) * 100) : 0;

  return (
    <div className="border p-4 rounded mt-6 bg-white shadow-sm">
      <h3 className="text-lg font-semibold mb-2">Progress</h3>

      <div className="space-y-1">
        <p><strong>Status:</strong> {data.status}</p>
        <p><strong>Processed:</strong> {data.processed}</p>
        <p><strong>Total:</strong> {data.total}</p>
        <p><strong>Chunks:</strong> {data.chunks}</p>
      </div>

      <div className="w-full bg-gray-200 h-3 rounded mt-3">
        <div
          className="bg-blue-500 h-3 rounded transition-all"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>

      <p className="mt-1 text-sm text-gray-600">{percentage}%</p>
    </div>
  );
}
