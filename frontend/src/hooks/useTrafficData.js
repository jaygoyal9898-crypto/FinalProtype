import { useEffect, useState } from "react";
import { getCurrentAnalysis } from "../api/traffic";

export function useTrafficData(intervalMs = 10000) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const result = await getCurrentAnalysis();
        if (!active) return;
        setAnalysis(result?.status === "empty" ? null : result);
        setError(null);
        setUpdatedAt(new Date());
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    const timer = setInterval(load, intervalMs);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [intervalMs]);

  return { analysis, loading, error, updatedAt, refresh: async () => {
    try {
      const result = await getCurrentAnalysis();
      setAnalysis(result?.status === "empty" ? null : result);
      setError(null);
      setUpdatedAt(new Date());
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      throw err;
    }
  }};
}
