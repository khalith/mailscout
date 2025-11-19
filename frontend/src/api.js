// frontend/src/api.js

// ALWAYS resolve a valid backend URL
export const API_URL =
  (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== "")
    ? import.meta.env.VITE_API_URL
    : "http://localhost:8000";

// Generic helpers
export async function apiPost(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body,
  });
  return res.json();
}

export async function apiGet(path) {
  const res = await fetch(`${API_URL}${path}`);
  return res.json();
}

// Specific endpoints
export const getUploadStatus = async (uploadId) => {
  const res = await fetch(`${API_URL}/uploads/status/${uploadId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
};

// ALWAYS return full backend URL
export const DOWNLOAD_RESULTS_API = `${API_URL}/results/download`;

export const UPLOAD_STATUS_API = `${API_URL}/uploads/status`;
