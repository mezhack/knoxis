import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useAuthStore } from "./useAuthStore";
import type { MeResponse } from "../lib/types";

export function useAuth() {
  const setAuth = useAuthStore((s) => s.setAuth);

  const query = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const data = await api.get<MeResponse>("/admin/me");
      setAuth(data.user, data.current_organization, data.role);
      return data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  return query;
}
