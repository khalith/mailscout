// export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// export async function apiPost(path, body) {
//   const res = await fetch(`${API_BASE}${path}`, {
//     method: "POST",
//     body
//   });
//   return res.json();
// }

// export async function apiGet(path) {
//   const res = await fetch(`${API_BASE}${path}`);
//   return res.json();
// }

// // Existing function you already had
// export const getUploadStatus = async (uploadId) => {
//   const res = await fetch(`${API_URL}/uploads/status/${uploadId}`);
//   if (!res.ok) throw new Error("Failed to fetch status");
//   return res.json();
// };

// const API_URL = import.meta.env.VITE_API_URL;

// // Generic GET
// export const apiGet = async (path) => {
//   const res = await fetch(`${API_URL}${path}`);
//   return res.json();
// };

// // Status endpoint
// export const UPLOAD_STATUS_API = `${API_URL}/uploads/status`;

// // Correct results download base
// export const DOWNLOAD_RESULTS_API = `${API_URL}/results/download`;
// ==============================
// BASE API URL
// ==============================
export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

// ==============================
// GENERIC HELPERS
// ==============================
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

// ==============================
// SPECIFIC API ENDPOINTS
// ==============================

// Upload processing status
export const getUploadStatus = async (uploadId) => {
  const res = await fetch(`${API_URL}/uploads/status/${uploadId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
};

// Correct results download base
export const DOWNLOAD_RESULTS_API = `${API_URL}/results/download`;

// Upload status base
export const UPLOAD_STATUS_API = `${API_URL}/uploads/status`;
