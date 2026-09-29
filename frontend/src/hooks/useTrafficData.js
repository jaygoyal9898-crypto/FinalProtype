import { useCallback, useEffect, useState } from "react";
import { getCurrentAnalysis } from "../api/traffic";

export function useTrafficData(intervalMs = 10000) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  const load = useCallback(async () => {
    try {
      const result = await getCurrentAnalysis();

      setAnalysis(result?.status === "empty" ? null : result);
      setError(null);
      setUpdatedAt(new Date());

      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : String(err);

      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    let timer = null;

    const poll = async () => {
      if (!active) return;

      try {
        const result = await getCurrentAnalysis();

        if (!active) return;

        setAnalysis(
          result?.status === "empty" ? null : result
        );
        setError(null);
        setUpdatedAt(new Date());

        /*
         * IMPORTANT:
         * Once analysis is completed, stop polling.
         * We do NOT start another video.
         */
        if (result?.status === "completed") {
          return;
        }

        /*
         * Continue polling only while the analysis
         * is still active.
         */
        if (
          result?.status === "queued" ||
          result?.status === "processing"
        ) {
          timer = setTimeout(poll, intervalMs);
          return;
        }

        /*
         * Empty/no analysis:
         * check again later.
         */
        if (!result || result?.status === "empty") {
          timer = setTimeout(poll, intervalMs);
        }
      } catch (err) {
        if (!active) return;

        setError(
          err instanceof Error ? err.message : String(err)
        );

        /*
         * Retry after an API error.
         */
        timer = setTimeout(poll, intervalMs);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    poll();

    return () => {
      active = false;

      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [intervalMs]);

  const refresh = useCallback(async () => {
    const result = await load();
    return result;
  }, [load]);

  return {
    analysis,
    loading,
    error,
    updatedAt,
    refresh,
  };
}