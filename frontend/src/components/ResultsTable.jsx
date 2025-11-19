// frontend/src/components/ResultsTable.jsx
import { useState } from "react";
import { DOWNLOAD_RESULTS_API } from "../api";

export default function ResultsTable({ uploadId, results = [] }) {
  const [format, setFormat] = useState("csv");

  const handleDownload = async () => {
    const url = `${DOWNLOAD_RESULTS_API}/${uploadId}?file_format=${format}`;

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
      link.download = `results_${uploadId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Download error:", err);
      alert("Something went wrong while downloading");
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-3 mb-4">
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
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Download
        </button>
      </div>

      <table className="min-w-full border border-gray-200 rounded">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-4 py-2">Email</th>
            <th className="border px-4 py-2">Normalized</th>
            <th className="border px-4 py-2">Status</th>
            <th className="border px-4 py-2">Score</th>
            <th className="border px-4 py-2">Checks</th>
            <th className="border px-4 py-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, idx) => (
            <tr key={r.email ?? idx} className="border">
              <td className="border px-4 py-2">{r.email}</td>
              <td className="border px-4 py-2">{r.normalized}</td>
              <td className="border px-4 py-2">{r.status}</td>
              <td className="border px-4 py-2">{r.score}</td>
              <td className="border px-4 py-2">{r.checks}</td>
              <td className="border px-4 py-2">{r.created_at}</td>
            </tr>
          ))}
          {results.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center p-4 text-gray-500">
                No rows to display.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
