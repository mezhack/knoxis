import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../../../lib/api";
import type { BallotData, BallotPosition } from "../../../lib/types";

export default function BallotPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const ballot: BallotData | undefined = location.state?.ballot;

  const [selections, setSelections] = useState<Record<number, Set<number>>>({});
  const [reviewing, setReviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState("");

  if (!ballot) {
    navigate(`/votar/${slug}`, { replace: true });
    return null;
  }

  const toggleCandidate = (posId: number, candId: number, maxSelect: number) => {
    setSelections((prev) => {
      const current = new Set(prev[posId] || []);
      if (current.has(candId)) {
        current.delete(candId);
      } else if (current.size < maxSelect) {
        current.add(candId);
      }
      return { ...prev, [posId]: current };
    });
  };

  const isPositionComplete = (pos: BallotPosition): boolean =>
    (selections[pos.id]?.size ?? 0) === pos.vacancies;

  const allComplete = ballot.positions.every(isPositionComplete);

  const handleSubmit = async () => {
    setSubmitting(true);
    setServerError("");
    try {
      const choices = ballot.positions.map((p) => ({
        position_id: p.id,
        candidate_ids: Array.from(selections[p.id] || []),
      }));
      await api.post("/public/ballot/submit", { choices });
      navigate("/votar/confirmacao");
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.data?.detail as string || err.message);
        setReviewing(false);
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-brand-700 text-white px-4 py-3 shadow-sm sticky top-0 z-10">
        <p className="text-xs text-brand-200">Escrutínio {ballot.escrutinio_number}</p>
        <h1 className="text-base font-semibold">Sua cédula</h1>
      </header>

      {reviewing ? (
        <div className="flex-1 px-4 py-6 max-w-lg mx-auto w-full">
          <h2 className="text-lg font-bold mb-4">Revisão do voto</h2>
          <p className="text-sm text-gray-500 mb-4">Confirme suas escolhas antes de enviar.</p>

          {ballot.positions.map((pos) => {
            const chosen = ballot.positions
              .find((p) => p.id === pos.id)
              ?.candidates.filter((c) => selections[pos.id]?.has(c.id)) || [];
            return (
              <div key={pos.id} className="card mb-4">
                <h3 className="font-semibold mb-2">{pos.name}</h3>
                <ul>
                  {chosen.map((c) => (
                    <li key={c.id} className="text-sm py-1 border-b last:border-0 flex items-center gap-2">
                      <span className="w-4 h-4 bg-brand-600 rounded-full inline-block flex-shrink-0" />
                      {c.name}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}

          {serverError && (
            <p className="error-msg mb-4" role="alert">{serverError}</p>
          )}

          <div className="sticky bottom-0 bg-gray-50 pt-3 pb-4 flex gap-3">
            <button
              className="btn-secondary flex-1"
              onClick={() => setReviewing(false)}
              disabled={submitting}
            >
              Voltar e editar
            </button>
            <button
              className="btn-primary flex-1"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? "Enviando..." : "Confirmar voto"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 pb-24">
          {ballot.positions.map((pos) => {
            const selected = selections[pos.id]?.size ?? 0;
            const complete = isPositionComplete(pos);

            return (
              <section key={pos.id} className="mb-0">
                {/* Contador sticky por cargo */}
                <div
                  className={`sticky top-[56px] z-10 px-4 py-2 flex items-center justify-between border-b ${complete ? "bg-green-50 border-green-200" : "bg-white border-gray-200"}`}
                  aria-live="polite"
                  aria-atomic="true"
                >
                  <span className="font-semibold text-gray-800">{pos.name}</span>
                  <span
                    className={`text-sm font-medium ${complete ? "text-green-700" : "text-brand-600"}`}
                    aria-label={`${selected} de ${pos.vacancies} selecionados`}
                  >
                    {selected}/{pos.vacancies} selecionados
                  </span>
                </div>

                <p className="px-4 py-2 text-sm text-gray-500 bg-gray-50">
                  Marque exatamente <strong>{pos.vacancies}</strong> candidato(s)
                </p>

                <ul className="divide-y divide-gray-100 bg-white">
                  {pos.candidates.map((c) => {
                    const checked = selections[pos.id]?.has(c.id) ?? false;
                    const disabled = !checked && selected >= pos.vacancies;

                    return (
                      <li key={c.id}>
                        <label
                          className={`flex items-center gap-4 px-4 py-4 cursor-pointer min-h-[56px] transition-colors ${
                            checked
                              ? "bg-brand-50"
                              : disabled
                              ? "opacity-40 cursor-not-allowed"
                              : "hover:bg-gray-50 active:bg-gray-100"
                          }`}
                          aria-disabled={disabled}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={disabled}
                            onChange={() => toggleCandidate(pos.id, c.id, pos.vacancies)}
                            className="w-5 h-5 accent-brand-600 flex-shrink-0"
                            aria-label={`${c.name}, ${checked ? "selecionado" : "não selecionado"}`}
                          />
                          <span className="text-base">{c.name}</span>
                        </label>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      )}

      {/* Botão sticky de confirmação */}
      {!reviewing && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_-2px_8px_rgba(0,0,0,0.1)] px-4 py-3">
          {serverError && <p className="error-msg mb-2" role="alert">{serverError}</p>}
          <button
            className="btn-primary w-full text-base"
            onClick={() => setReviewing(true)}
            disabled={!allComplete}
            aria-disabled={!allComplete}
          >
            Revisar e confirmar voto
          </button>
          {!allComplete && (
            <p className="text-xs text-center text-gray-400 mt-1">
              Complete todos os cargos para continuar
            </p>
          )}
        </div>
      )}
    </div>
  );
}
