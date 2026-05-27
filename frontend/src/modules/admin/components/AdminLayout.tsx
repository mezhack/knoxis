import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { useAuthStore } from "../../../hooks/useAuthStore";

export default function AdminLayout() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { user, organization } = useAuthStore();
  const clear = useAuthStore((s) => s.clear);

  const logout = useMutation({
    mutationFn: () => api.post("/admin/auth/logout"),
    onSuccess: () => {
      clear();
      qc.clear();
      navigate("/login");
    },
  });

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-brand-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <NavLink to="/" className="font-bold text-xl no-underline text-white">
              Knoxis
            </NavLink>
            {organization && (
              <span className="text-brand-200 text-sm hidden sm:block">
                {organization.name}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-brand-200 hidden md:block">{user?.name}</span>
            <button
              onClick={() => logout.mutate()}
              className="text-sm text-white border border-brand-400 rounded px-3 py-1 hover:bg-brand-600 transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <ul className="flex gap-1">
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `block px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? "border-brand-600 text-brand-700"
                      : "border-transparent text-gray-600 hover:text-gray-900"
                  }`
                }
              >
                Eleições
              </NavLink>
            </li>
          </ul>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
