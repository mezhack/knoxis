import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import type { ParciaisData } from "../../../lib/types";
import { useAuth } from "../../../hooks/useAuth";

export default function EscrutinioParciaisPage() {
  const { id } = useParams();
  const { isError: authError } = useAuth();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["escrutinio", id, "parciais"],
    queryFn: () => api.get<ParciaisData>(`/admin/escrutinios/${id}/parciais`),
    refetchInterval: 3000,
    enabled: !authError,
  });

  if (authError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="card text-center">
          <p className="text-red-600 font-semibold">Acesso restrito. Faça login para ver os parciais.</p>
        </div>
      </div>
    );
  }

  if (isLoading) return <div className="p-8 text-gray-500">Carregando parciais...</div>;
  if (isError) return <div className="p-8 text-red-500">Escrutínio não encontrado ou não está aberto.</div>;
  if (!data) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Parciais — Escrutínio {id}</h1>
            <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded font-medium">
              PARCIAIS — NÃO DIVULGAR
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Atualiza a cada 3 segundos · {data.voters_so_far} votante(s) até agora
          </p>
        </div>

        <div className="space-y-4">
          {data.positions.map((p) => (
            <div key={p.position.id} className="card">
              <h2 className="font-semibold mb-1">{p.position.name}</h2>
              <p className="text-xs text-gray-400 mb-3">{p.position.vacancies_remaining} vaga(s)</p>
              <ul className="space-y-2">
                {p.candidates.map((c, idx) => {
                  const max = p.candidates[0]?.votes || 1;
                  const pct = max > 0 ? (c.votes / max) * 100 : 0;
                  return (
                    <li key={c.id}>
                      <div className="flex justify-between text-sm mb-1">
                        <span>{idx + 1}. {c.name}</span>
                        <span className="font-semibold">{c.votes}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
