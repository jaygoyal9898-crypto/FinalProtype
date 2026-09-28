import { useEffect, useState } from "react";
import { getAlerts } from "../api/alerts";

export function useAlerts() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    let active = true;
    getAlerts()
      .then((result) => {
        if (active) setAlerts(Array.isArray(result) ? result : result?.alerts || []);
      })
      .catch(() => {
        if (active) setAlerts([]);
      });
    return () => { active = false; };
  }, []);

  return { alerts };
}
