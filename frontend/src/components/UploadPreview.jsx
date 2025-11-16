// frontend/src/components/UploadPreview.jsx
import React, { useEffect, useState } from "react";

/**
 * UploadPreview
 *
 * Props:
 * - file: File object (CSV)
 * - maxPreviewRows: number (optional, default 10)
 * - onConfirm: function({ columnIndex, header, previewEmails }) called when user confirms the mapping
 *
 * Behavior:
 * - Parses the CSV client-side (simple CSV parsing, not full RFC compliant but handles typical CSVs)
 * - Shows first N rows as a preview table
 * - Tries to auto-detect email column by regex
 * - Lets user pick which column contains emails
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function simpleCsvParse(text, maxRows = 1000) {
  // Very lightweight CSV parser which:
  // - Splits on newlines
  // - Handles quoted fields (basic)
  // - Not fully RFC compliant but fine for preview / small files
  const rows = [];
  const lines = text.split(/\r\n|\n|\r/);
  for (let line of lines) {
    if (!line) {
      rows.push([]);
      continue;
    }
    const row = [];
    let cur = "";
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"' && line[i + 1] === '"') {
        // escaped quote
        cur += '"';
        i++;
        continue;
      }
      if (ch === '"') {
        inQuote = !inQuote;
        continue;
      }
      if (ch === "," && !inQuote) {
        row.push(cur);
        cur = "";
        continue;
      }
      cur += ch;
    }
    row.push(cur);
    rows.push(row);
    if (rows.length >= maxRows) break;
  }
  return rows;
}

export default function UploadPreview({ file, maxPreviewRows = 10, onConfirm }) {
  const [rows, setRows] = useState([]);
  const [headerRow, setHeaderRow] = useState(null);
  const [selectedCol, setSelectedCol] = useState(null);
  const [inferredCol, setInferredCol] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // parse file when it changes
  useEffect(() => {
    if (!file) {
      setRows([]);
      setHeaderRow(null);
      setSelectedCol(null);
      setInferredCol(null);
      return;
    }
    setLoading(true);
    setError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const parsed = simpleCsvParse(text, maxPreviewRows + 1); // +1 for header guess
        if (!parsed || parsed.length === 0) {
          setRows([]);
          setHeaderRow(null);
          setLoading(false);
          return;
        }

        // assume first row is header if looks like strings (heuristic)
        const first = parsed[0] || [];
        const second = parsed[1] || [];
        let hasHeader = false;
        // decide header: if first row contains any non-email and includes alpha-only cells, treat as header
        const alphaCount = first.filter((c) => /^[A-Za-z _-]+$/.test((c || "").trim())).length;
        const emailLikeCountFirst = first.filter((c) => EMAIL_RE.test((c || "").trim())).length;
        const emailLikeCountSecond = second.filter((c) => EMAIL_RE.test((c || "").trim())).length;
        if (alphaCount >= 1 && emailLikeCountSecond >= emailLikeCountFirst) {
          hasHeader = true;
        }

        let header = null;
        let dataRows = parsed;
        if (hasHeader) {
          header = first.map((c) => (c === undefined ? "" : c));
          dataRows = parsed.slice(1);
        } else {
          const cols = first.length;
          header = new Array(cols).fill("").map((_, i) => `Column ${i + 1}`);
        }

        // Limit preview rows
        const previewRows = dataRows.slice(0, maxPreviewRows);

        // detect email column by scoring columns with regex matches
        const colScores = [];
        const colCount = Math.max(...previewRows.map((r) => r.length), header.length);
        for (let ci = 0; ci < colCount; ci++) {
          let score = 0;
          for (let r of previewRows) {
            const cell = (r[ci] || "").trim();
            if (EMAIL_RE.test(cell)) score += 2;
            // partial if contains @
            else if (cell.includes("@")) score += 1;
          }
          // small boost if header includes 'email'
          const head = (header[ci] || "").toLowerCase();
          if (head.includes("email")) score += 3;
          colScores.push(score);
        }

        // pick highest scoring column
        let best = -1;
        let bestScore = -1;
        colScores.forEach((s, idx) => {
          if (s > bestScore) {
            bestScore = s;
            best = idx;
          }
        });

        setRows(previewRows);
        setHeaderRow(header);
        setInferredCol(best >= 0 ? best : null);
        setSelectedCol(best >= 0 ? best : 0);
      } catch (err) {
        setError("Failed to parse CSV file. Make sure it's a valid CSV (UTF-8).");
      } finally {
        setLoading(false);
      }
    };
    reader.onerror = () => {
      setError("Failed to read file.");
      setLoading(false);
    };

    // read only first ~200KB for quick preview
    const slice = file.slice(0, 200 * 1024);
    reader.readAsText(slice, "utf-8");

    // cleanup not strictly necessary
    return () => {
      reader.abort && reader.abort();
    };
  }, [file, maxPreviewRows]);

  const handleConfirm = () => {
    if (!headerRow) return;
    const colIdx = selectedCol;
    // assemble preview emails (first N non-empty values)
    const previewEmails = [];
    for (let r of rows) {
      const val = (r[colIdx] || "").trim();
      if (val) previewEmails.push(val);
      if (previewEmails.length >= 10) break;
    }
    onConfirm && onConfirm({ columnIndex: colIdx, header: headerRow[colIdx] || "", previewEmails });
  };

  if (!file) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl bg-white shadow rounded p-6">
      <div className="mb-4">
        <div className="text-sm text-gray-600">Preview: <strong>{file.name}</strong></div>
      </div>

      {loading && (
        <div className="py-6 text-center text-gray-600">Parsing file preview…</div>
      )}

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded mb-4">{error}</div>
      )}

      {!loading && headerRow && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Select email column</label>
              <select
                value={selectedCol}
                onChange={(e) => setSelectedCol(parseInt(e.target.value, 10))}
                className="mt-1 block rounded-md border-gray-200 shadow-sm"
              >
                {headerRow.map((h, idx) => (
                  <option key={idx} value={idx}>
                    {h || `Column ${idx + 1}`} {inferredCol === idx ? "— detected" : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-sm text-gray-600">
              Detected column: <strong>{inferredCol !== null ? (headerRow[inferredCol] || `Column ${inferredCol+1}`) : "—"}</strong>
            </div>
          </div>

          <div className="overflow-x-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  {headerRow.map((h, idx) => (
                    <th
                      key={idx}
                      className={`px-3 py-2 ${selectedCol === idx ? "bg-blue-50" : ""}`}
                    >
                      {h || `Column ${idx + 1}`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, ri) => (
                  <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                    {headerRow.map((_, ci) => {
                      const val = r[ci] || "";
                      const isEmail = EMAIL_RE.test((val || "").trim());
                      return (
                        <td key={ci} className="px-3 py-2 align-top">
                          <div className="text-sm">
                            <span className={isEmail ? "text-green-700 font-medium" : "text-gray-800"}>
                              {val}
                            </span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing first {rows.length} rows
            </div>
            <div>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 bg-blue-600 text-white rounded mr-2"
              >
                Confirm column & continue
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
