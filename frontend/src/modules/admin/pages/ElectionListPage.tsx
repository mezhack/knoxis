import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import type { Election } from "../../../lib/types";

const STATUS_LABEL: Record<string, string> = {
  rascunho: "Rascunho",
  pronta: "Pronta",
  em_andamento: "Em andamento",
  encerrada: "Encerrada",
  cancelada: "Cancelada",
};

const STATUS_COLOR: Record<string, string> = {
  rascunho: "bg-gray-100 text-gray-700",
  pronta: "bg-blue-100 text-blue-700",
  em_andamento: "bg-green-100 text-green-700",
  encerrada: "bg-purple-100 text-purple-700",
  cancelada: "bg-red-100 text-red-700",
};

export default function ElectionListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["elections"],
    queryFn: () => api.get<{ items: Election[] }>("/admin/elections"),
  });

  if (isLoading) return <div className="text-gray-500">Carregando eleições...</div>;
  if (isError) return <div className="text-red-600">Erro ao carregar eleições.</div>;

  const elections = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Eleições</h1>
        <Link to="/eleicoes/nova" className="btn-primary no-underline">
          Nova eleição
        </Link>
      </div>

      {elections.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 mb-4">Nenhuma eleição criada ainda.</p>
          <Link to="/eleicoes/nova" className="btn-primary no-underline inline-block">
            Criar primeira eleição
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {elections.map((e) => (
            <Link
              key={e.id}
              to={`/eleicoes/${e.id}`}
              className="card flex items-center justify-between hover:shadow-md transition-shadow no-underline"
            >
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="font-semibold text-gray-900">{e.name}</h2>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[e.status]}`}>
                    {STATUS_LABEL[e.status]}
                  </span>
                </div>
                <div className="text-sm text-gray-500 flex gap-4">
                  <span>{e.positions_count ?? 0} cargo(s)</span>
                  <span>{e.voters_count ?? 0} votante(s)</span>
                  {e.scheduled_for && <span>Data: {e.scheduled_for}</span>}
                  {e.current_escrutinio_number && (
                    <span className="text-green-700 font-medium">
                      Escrutínio {e.current_escrutinio_number} aberto
                    </span>
                  )}
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
