import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";
import type { CloseResult, EscrutinioDetail, Election } from "../../../lib/types";

export default function EscrutinioResultadoPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [result, setResult] = useState<CloseResult | null>(null);
  const [confirmClose, setConfirmClose] = useState(false);
  const [serverError, setServerError] = useState("");
  const [nextIsFinale, setNextIsFinale] = useState(false);

  const { data: esc } = useQuery({
    queryKey: ["escrutinios", id],
    queryFn: () => api.get<EscrutinioDetail & { election_id?: number }>(`/admin/escrutinios/${id}`),
  });

  const closeEsc = useMutation({
    mutationFn: () => api.post<CloseResult>(`/admin/escrutinios/${id}/close`, { confirm: true }),
    onSuccess: (data) => {
      setResult(data);
      qc.invalidateQueries({ queryKey: ["elections"] });
    },
    onError: (err) => {
      if (err instanceof ApiError) setServerError(err.message);
    },
  });

  const createNext = useMutation({
    mutationFn: () =>
      api.post(`/admin/elections/${esc?.election_id ?? ""}/escrutinios`, { is_final: nextIsFinale }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["elections"] });
      navigate(-1);
    },
    onError: (err) => {
      if (err instanceof ApiError) setServerError(err.message);
    },
  });

  if (!esc) return <div>Carregando...</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-gray-500 hover:text-gray-700">← Voltar</button>
        <h1 className="text-xl font-bold">Escrutínio {esc.number}</h1>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${esc.status === "aberto" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
          {esc.status}
        </span>
      </div>

      {esc.status === "aberto" && !result && (
        <div className="card">
          <h2 className="font-semibold mb-3">Encerrar escrutínio</h2>
          <p className="text-gray-600 text-sm mb-4">
            Ao encerrar, a apuração será calculada e os eleitos definidos. Esta ação é irreversível.
          </p>
          {!confirmClose ? (
            <button className="btn-danger" onClick={() => setConfirmClose(true)}>
              Encerrar escrutínio
            </button>
          ) : (
            <div className="flex gap-3">
              <button
                className="btn-danger"
                onClick={() => closeEsc.mutate()}
                disabled={closeEsc.isPending}
              >
                {closeEsc.isPending ? "Encerrando..." : "Confirmar encerramento"}
              </button>
              <button className="btn-secondary" onClick={() => setConfirmClose(false)}>Cancelar</button>
            </div>
          )}
          {serverError && <p className="error-msg mt-2">{serverError}</p>}
        </div>
      )}

      {result && (
        <div className="card">
          <h2 className="font-semibold mb-1 text-green-800">Escrutínio encerrado</h2>
          <p className="text-sm text-gray-500 mb-4">Total de votantes: {result.escrutinio.total_voters}</p>

          {result.results.map((pr) => (
            <div key={pr.position.id} className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-2">{pr.position.name}</h3>
              <p className="text-xs text-gray-400 mb-2">
                {pr.threshold ? `Limiar: ${pr.threshold} votos` : "Escrutínio final — mais votados"} · Vagas restantes: {pr.remaining_vacancies}
              </p>
              {pr.tie_pending && (
                <div className="mb-2 p-2 bg-yellow-50 border border-yellow-300 rounded text-sm text-yellow-800">
                  Empate na linha de corte — resolução necessária antes do próximo escrutínio.
                </div>
              )}
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="pb-1">Candidato</th>
                    <th className="pb-1">Votos</th>
                    <th className="pb-1">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {pr.candidates.map((c) => (
                    <tr
                      key={c.id}
                      className={`border-b last:border-0 ${c.elected ? "bg-green-50 font-semibold" : ""} ${c.tie_at_cutoff ? "bg-yellow-50" : ""}`}
                    >
                      <td className="py-2">{c.name}</td>
                      <td className="py-2">{c.votes}</td>
                      <td className="py-2">
                        {c.elected ? "✓ Eleito" : c.tie_at_cutoff ? "⚠ Empate" : "Remanescente"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}

          {result.election_status === "encerrada" ? (
            <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded text-center">
              <p className="font-semibold text-purple-800">Eleição encerrada! Todas as vagas foram preenchidas.</p>
              <Link to="/" className="btn-primary mt-3 inline-block no-underline">Voltar ao painel</Link>
            </div>
          ) : (
            <div className="mt-4 border-t pt-4">
              <h3 className="font-medium mb-3">Iniciar próximo escrutínio</h3>
              <label className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  checked={nextIsFinale}
                  onChange={(e) => setNextIsFinale(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Marcar como escrutínio final (mais votados)</span>
              </label>
              <button
                className="btn-primary"
                onClick={() => createNext.mutate()}
                disabled={createNext.isPending}
              >
                {createNext.isPending ? "Criando..." : "Criar próximo escrutínio"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Show current results if already closed */}
      {esc.status === "encerrado" && !result && (
        <div className="card text-center text-gray-500">
          <p>Escrutínio já encerrado. Ver relatório para detalhes.</p>
        </div>
      )}
    </div>
  );
}
