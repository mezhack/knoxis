import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";
import type { Candidate, Election, Escrutinio, Position, Voter } from "../../../lib/types";

export default function ElectionDashboardPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [newPosition, setNewPosition] = useState({ name: "", vacancies: 1 });
  const [newCandidate, setNewCandidate] = useState<Record<number, string>>({});
  const [importResult, setImportResult] = useState<null | { imported: number; skipped_duplicate: number; skipped_invalid: number; errors: { line: number; reason: string; value_last2: string }[] }>(null);
  const [serverError, setServerError] = useState("");

  const { data: election, isLoading } = useQuery({
    queryKey: ["elections", id],
    queryFn: () => api.get<Election>(`/admin/elections/${id}`),
  });

  const { data: voters } = useQuery({
    queryKey: ["elections", id, "voters"],
    queryFn: () => api.get<{ results: Voter[] }>(`/admin/elections/${id}/voters`),
  });

  const { data: escrutinios } = useQuery({
    queryKey: ["elections", id, "escrutinios"],
    queryFn: () => api.get<Escrutinio[]>(`/admin/elections/${id}/escrutinios`),
    enabled: election?.status === "em_andamento" || election?.status === "encerrada",
  });

  const addPosition = useMutation({
    mutationFn: () =>
      api.post<Position>(`/admin/elections/${id}/positions`, newPosition),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["elections", id] });
      setNewPosition({ name: "", vacancies: 1 });
    },
  });

  const deletePosition = useMutation({
    mutationFn: (posId: number) => api.delete(`/admin/positions/${posId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["elections", id] }),
  });

  const addCandidate = useMutation({
    mutationFn: ({ posId, name }: { posId: number; name: string }) =>
      api.post(`/admin/positions/${posId}/candidates`, { name }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["elections", id] });
      setNewCandidate({});
    },
  });

  const deleteCandidate = useMutation({
    mutationFn: (cId: number) => api.delete(`/admin/candidates/${cId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["elections", id] }),
  });

  const startElection = useMutation({
    mutationFn: () => api.post(`/admin/elections/${id}/start`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["elections", id] });
      setServerError("");
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        const fields = err.data?.fields as any;
        setServerError(fields?.requisitos?.join("\n") || err.message);
      }
    },
  });

  const openEscrutinio = useMutation({
    mutationFn: (escId: number) => api.post(`/admin/escrutinios/${escId}/open`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["elections", id, "escrutinios"] }),
  });

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    try {
      const result = await api.postForm<typeof importResult>(`/admin/elections/${id}/voters/import`, form);
      setImportResult(result);
      qc.invalidateQueries({ queryKey: ["elections", id, "voters"] });
      qc.invalidateQueries({ queryKey: ["elections", id] });
    } catch (err) {
      if (err instanceof ApiError) setServerError(err.message);
    }
  };

  if (isLoading || !election) return <div>Carregando...</div>;

  const isEditable = election.status === "rascunho" || election.status === "pronta";
  const isInProgress = election.status === "em_andamento";
  const publicUrl = election.positions?.length
    ? `${window.location.origin}/votar/${qc.getQueryData<any>(["me"])?.current_organization?.slug}`
    : null;

  const openEscrutinio_ = escrutinios?.find((e) => e.status === "aberto");
  const preparandoEscrutinio = escrutinios?.find((e) => e.status === "preparando");

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">← Eleições</Link>
          </div>
          <h1 className="text-2xl font-bold mt-1">{election.name}</h1>
          <p className="text-gray-500 text-sm">Status: <strong>{election.status}</strong> · {election.voters_count ?? 0} votante(s)</p>
        </div>
        <div className="flex gap-2">
          {isEditable && (
            <Link to={`/eleicoes/${id}/editar`} className="btn-secondary no-underline">Editar</Link>
          )}
          {(election.status === "rascunho" || election.status === "pronta") && (
            <button
              className="btn-primary"
              onClick={() => startElection.mutate()}
              disabled={startElection.isPending}
            >
              Iniciar eleição
            </button>
          )}
        </div>
      </div>

      {serverError && (
        <div className="card bg-red-50 border-red-200 text-red-700 whitespace-pre-wrap">{serverError}</div>
      )}

      {isInProgress && openEscrutinio_ && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-green-800">Escrutínio {openEscrutinio_.number} — Aberto</p>
              <p className="text-sm text-green-700">{openEscrutinio_.voters_so_far ?? 0} voto(s) registrado(s)</p>
            </div>
            <div className="flex gap-2">
              <a
                href={`/escrutinios/${openEscrutinio_.id}/parciais`}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary no-underline text-sm"
              >
                Ver parciais (nova aba)
              </a>
              <Link to={`/escrutinios/${openEscrutinio_.id}/resultado`} className="btn-primary no-underline text-sm">
                Encerrar escrutínio
              </Link>
            </div>
          </div>
          {publicUrl && (
            <p className="text-sm text-green-700 mt-2">URL pública: <strong>{publicUrl}</strong></p>
          )}
        </div>
      )}

      {isInProgress && !openEscrutinio_ && preparandoEscrutinio && (
        <div className="card bg-blue-50 border-blue-200">
          <p className="font-semibold text-blue-800">Escrutínio {preparandoEscrutinio.number} — Preparando</p>
          {preparandoEscrutinio.is_final && <p className="text-sm text-blue-700">Este é o escrutínio final.</p>}
          <button
            className="btn-primary mt-3"
            onClick={() => openEscrutinio.mutate(preparandoEscrutinio.id)}
            disabled={openEscrutinio.isPending}
          >
            Abrir escrutínio
          </button>
        </div>
      )}

      {/* Relatórios */}
      {escrutinios && escrutinios.some((e) => e.status === "encerrado") && (
        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Relatórios</h2>
            <Link to={`/eleicoes/${id}/relatorios`} className="btn-secondary no-underline text-sm">
              Ver relatórios
            </Link>
          </div>
        </div>
      )}

      {/* Cargos */}
      <div className="card">
        <h2 className="font-semibold mb-4">Cargos e candidatos</h2>
        {election.positions?.map((pos) => (
          <div key={pos.id} className="mb-6 border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="font-medium">{pos.name}</span>
                <span className="text-sm text-gray-500 ml-2">({pos.vacancies} vaga(s))</span>
              </div>
              {isEditable && (
                <button
                  className="text-red-500 text-sm hover:underline"
                  onClick={() => deletePosition.mutate(pos.id)}
                >
                  Remover cargo
                </button>
              )}
            </div>

            <CandidateList
              positionId={pos.id}
              electionId={Number(id)}
              isEditable={isEditable}
              onDelete={(cId) => deleteCandidate.mutate(cId)}
              onAdd={(name) => addCandidate.mutate({ posId: pos.id, name })}
              newName={newCandidate[pos.id] ?? ""}
              onNameChange={(v) => setNewCandidate((prev) => ({ ...prev, [pos.id]: v }))}
            />
          </div>
        ))}

        {isEditable && (
          <div className="border-t pt-4 mt-4">
            <h3 className="text-sm font-medium mb-2">Adicionar cargo</h3>
            <div className="flex gap-2">
              <input
                type="text"
                className="input flex-1"
                placeholder="Ex.: Presbítero"
                value={newPosition.name}
                onChange={(e) => setNewPosition((p) => ({ ...p, name: e.target.value }))}
              />
              <input
                type="number"
                className="input w-24"
                placeholder="Vagas"
                min={1}
                value={newPosition.vacancies}
                onChange={(e) => setNewPosition((p) => ({ ...p, vacancies: parseInt(e.target.value) || 1 }))}
              />
              <button
                className="btn-primary"
                onClick={() => addPosition.mutate()}
                disabled={!newPosition.name || addPosition.isPending}
              >
                Adicionar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Votantes */}
      <div className="card">
        <h2 className="font-semibold mb-4">Lista de votantes ({election.voters_count ?? 0})</h2>

        {isEditable && (
          <div className="mb-4">
            <label className="btn-secondary cursor-pointer inline-block">
              Importar CSV (cpf, nome)
              <input type="file" accept=".csv" className="hidden" onChange={handleImport} />
            </label>
            <p className="text-xs text-gray-400 mt-1">CSV com cabeçalho: cpf,nome</p>
          </div>
        )}

        {importResult && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-sm">
            <p className="font-medium text-green-800">Importação concluída</p>
            <p>Importados: {importResult.imported} · Duplicados: {importResult.skipped_duplicate} · Inválidos: {importResult.skipped_invalid}</p>
            {importResult.errors.length > 0 && (
              <details className="mt-2">
                <summary className="cursor-pointer text-red-600">Ver erros ({importResult.errors.length})</summary>
                <ul className="mt-1 space-y-1">
                  {importResult.errors.map((err, i) => (
                    <li key={i}>Linha {err.line}: {err.reason} (terminação -{err.value_last2})</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}

        {voters?.results?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="pb-2">Nome</th>
                  <th className="pb-2">CPF</th>
                </tr>
              </thead>
              <tbody>
                {voters.results.map((v) => (
                  <tr key={v.id} className="border-b last:border-0">
                    <td className="py-2">{v.name}</td>
                    <td className="py-2 text-gray-500">{v.cpf_masked}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Nenhum votante importado.</p>
        )}
      </div>
    </div>
  );
}

function CandidateList({
  positionId,
  electionId,
  isEditable,
  onDelete,
  onAdd,
  newName,
  onNameChange,
}: {
  positionId: number;
  electionId: number;
  isEditable: boolean;
  onDelete: (id: number) => void;
  onAdd: (name: string) => void;
  newName: string;
  onNameChange: (v: string) => void;
}) {
  const { data } = useQuery({
    queryKey: ["positions", positionId, "candidates"],
    queryFn: () => api.get<Candidate[]>(`/admin/positions/${positionId}/candidates`),
  });

  const candidates = Array.isArray(data) ? data : [];

  return (
    <div>
      <ul className="space-y-1 mb-2">
        {candidates.map((c) => (
          <li key={c.id} className="flex items-center justify-between text-sm">
            <span>{c.name}</span>
            {isEditable && (
              <button className="text-red-400 hover:text-red-600 text-xs" onClick={() => onDelete(c.id)}>
                Remover
              </button>
            )}
          </li>
        ))}
      </ul>
      {isEditable && (
        <div className="flex gap-2 mt-2">
          <input
            type="text"
            className="input flex-1 text-sm"
            placeholder="Nome do candidato"
            value={newName}
            onChange={(e) => onNameChange(e.target.value)}
          />
          <button
            className="btn-secondary text-sm"
            onClick={() => {
              if (newName.trim()) onAdd(newName.trim());
            }}
            disabled={!newName.trim()}
          >
            + Candidato
          </button>
        </div>
      )}
    </div>
  );
}
