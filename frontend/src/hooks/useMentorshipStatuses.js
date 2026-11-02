import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";

// The mentee's most relevant request for each mentor: accepted first, then
// pending, otherwise the latest declined one.
const rank = { accepted: 3, pending: 2, declined: 1 };

export default function useMentorshipStatuses() {
  const [byMentor, setByMentor] = useState({});

  const reload = useCallback(async () => {
    try {
      const requests = await apiRequest("/api/mentorships/outgoing");
      const next = {};
      for (const request of requests) {
        const current = next[request.mentor_id];
        if (!current || rank[request.status] > rank[current.status]) next[request.mentor_id] = request;
      }
      setByMentor(next);
    } catch {
      // Status badges are an enhancement; the list still works without them.
    }
  }, []);

  useEffect(() => { queueMicrotask(() => { void reload(); }); }, [reload]);

  return { byMentor, reload };
}
