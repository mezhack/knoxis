import { create } from "zustand";
import type { Organization, User } from "../lib/types";

interface AuthState {
  user: User | null;
  organization: Organization | null;
  role: string | null;
  setAuth: (user: User, org: Organization | null, role: string) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  organization: null,
  role: null,
  setAuth: (user, organization, role) => set({ user, organization, role }),
  clear: () => set({ user: null, organization: null, role: null }),
}));
