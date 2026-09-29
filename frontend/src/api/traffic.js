import { apiFetch } from "./client";

export async function getCurrentAnalysis() {
  const response = await fetch("/current-analysis");

  if (!response.ok) {
    throw new Error(`Failed to fetch current analysis: ${response.status}`);
  }

  return response.json();
}

export async function startLive() {
  return apiFetch("/start-live", {
    method: "POST",
  });
}

export async function restartLive() {
  return apiFetch("/restart-live", {
    method: "POST",
  });
}