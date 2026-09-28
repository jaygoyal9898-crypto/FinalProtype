import { apiFetch } from "./client";

export async function getCurrentAnalysis() {
  return apiFetch("/current-analysis");
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