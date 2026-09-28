import { apiRequest, getRecommendations } from "./traffic";

export async function getAlerts() {
  try {
    return await apiRequest("/alerts");
  } catch {
    return [];
  }
}

export async function getAnalysisRecommendations(analysisId) {
  return getRecommendations(analysisId);
}
