// frontend/src/api.js

// FORCE backend URL — NEVER allow undefined
export const API_URL =
  (typeof import.meta.env.VITE_API_URL === "string" &&
    import.meta.env.VITE_API_URL.trim() !== "" &&
    import.meta.env.VITE_API_URL.trim() !== "undefined" &&
    import.meta.env.VITE_API_URL.trim() !== "null")
    ? import.meta.env.VITE_API_URL.trim()
    : "http://localhost:8000";   // SAFE fallback

console.log(">>>> USING API_URL =", API_URL); // DEBUG — verify in DevTools

// Generic POST
export async function apiPost(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body,
  });
  return res.json();
}

// Generic GET
export async function apiGet(path) {
  const res = await fetch(`${API_URL}${path}`);
  return res.json();
}

// Upload status
export const UPLOAD_STATUS_API = `${API_URL}/uploads/status`;

// DOWNLOAD endpoint — ALWAYS correct because API_URL is forced
export const DOWNLOAD_RESULTS_API = `${API_URL}/results/download`;
