import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import type { RelatorioData } from "../../../lib/types";
import "../../../styles/print.css";

interface RelatorioItemProps {
  escrutinioId: number;
}

function RelatorioItem({ escrutinioId }: RelatorioItemProps) {
  const { data } = useQuery({
    queryKey: ["relatorio", escrutinioId],
    queryFn: () => api.get<RelatorioData>(`/admin/escrutinios/${escrutinioId}/relatorio`),
  });

  if (!data) return <div className="text-gray-400 text-sm">Carregando...</div>;

  return (
    <div className="print-container mb-8 page-break-before">
      <div className="mb-4">
        <h2 className="text-xl font-bold">{data.election.name}</h2>
        <p className="text-gray-600">
          {data.election.organization.name}
          {data.election.organization.city && ` — ${data.election.organization.city}/${data.election.organization.state}`}
        </p>
        <p className="text-gray-600">
          Escrutínio nº {data.escrutinio.number}
          {data.escrutinio.is_final ? " (Final)" : ""}
          {" · "}{data.escrutinio.opened_at && new Date(data.escrutinio.opened_at).toLocaleDateString("pt-BR")}
        </p>
        <p className="text-gray-600">
          Total de votantes: <strong>{data.totals.voters}</strong>
          {data.totals.abstention != null && data.totals.abstention >= 0 && (
            <> · Abstenções: <strong>{data.totals.abstention}</strong></>
          )}
        </p>
      </div>

      {data.positions.map((p) => (
        <div key={p.position.id} className="mb-6">
          <h3 className="font-semibold text-lg border-b pb-1 mb-2">
            {p.position.name} — {p.vacancies_in_round} vaga(s)
            {p.threshold && <span className="font-normal text-sm ml-2">(Limiar: {p.threshold} votos)</span>}
          </h3>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2 text-left">Candidato</th>
                <th className="border border-gray-300 p-2 text-right">Votos</th>
                <th className="border border-gray-300 p-2 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {p.candidates.map((c) => (
                <tr key={c.id} className={c.elected ? "elected-row" : ""}>
                  <td className="border border-gray-300 p-2">{c.name}</td>
                  <td className="border border-gray-300 p-2 text-right">{c.votes}</td>
                  <td className="border border-gray-300 p-2 text-center">
                    {c.elected ? "Eleito" : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

export default function RelatorioImpressoPage() {
  const { id } = useParams();

  const { data: list } = useQuery({
    queryKey: ["relatorios", id],
    queryFn: () => api.get<any[]>(`/admin/elections/${id}/relatorios`),
  });

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6 no-print">
        <h1 className="text-2xl font-bold">Relatórios da eleição</h1>
        <button className="btn-primary" onClick={() => window.print()}>
          Imprimir
        </button>
      </div>

      {!list?.length ? (
        <div className="card text-center text-gray-400">
          Nenhum escrutínio encerrado.
        </div>
      ) : (
        list.map((item) => <RelatorioItem key={item.id} escrutinioId={item.id} />)
      )}
    </div>
  );
}
