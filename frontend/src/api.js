export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body
  });
  return res.json();
}

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}

// frontend/src/api.js

const API_URL = import.meta.env.VITE_API_URL;

export const getUploadStatus = async (uploadId) => {
  const res = await fetch(`${API_URL}/uploads/status/${uploadId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
};
