// frontend/src/api.js

export const API_URL = (() => {
  // 1. Use Vite env if it exists at build time
  const v = import.meta.env.VITE_API_URL;
  if (typeof v === "string" && v.trim() !== "") {
    return v.trim();
  }

  // 2. Runtime fallback on Fly.io (production)
  if (typeof window !== "undefined") {
    const host = window.location.hostname;

    if (host.endsWith("fly.dev")) {
      return "https://mailscout-backend.fly.dev";
    }
  }

  // 3. Local dev fallback
  return "";
})();


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
