import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";
import type { PublicElectionData } from "../../../lib/types";
import { applyMask, isValid } from "../../../lib/cpf";

const schema = z.object({
  cpf: z.string().refine((v) => isValid(v), "CPF inválido"),
});

type FormData = z.infer<typeof schema>;

export default function ElectionEntryPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const [cpfValue, setCpfValue] = useState("");

  const { data: electionData } = useQuery({
    queryKey: ["public-election", slug],
    queryFn: () => api.get<PublicElectionData>(`/public/elections/${slug}`),
  });

  const { handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { cpf: "" },
  });

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const masked = applyMask(e.target.value);
    setCpfValue(masked);
    setValue("cpf", masked);
  };

  const onSubmit = async (data: FormData) => {
    setServerError("");
    try {
      const result = await api.post<{ ballot: { escrutinio_number: number; positions: any[] } }>(
        `/public/elections/${slug}/identify`,
        { cpf: data.cpf }
      );
      navigate(`/votar/${slug}/cedula`, { state: { ballot: result.ballot } });
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.data?.detail as string || err.message);
      }
    }
  };

  const election = electionData?.election;
  const esc = electionData?.current_escrutinio;
  const isOpen = esc?.status === "aberto";

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header minimalista */}
      <header className="bg-brand-700 text-white px-4 py-3 shadow-sm">
        <p className="text-xs text-brand-200">{election?.organization_name}</p>
        <h1 className="text-base font-semibold leading-tight">{election?.name || "Carregando..."}</h1>
        {esc && <p className="text-xs text-brand-200">Escrutínio {esc.number}</p>}
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        <div className="w-full max-w-sm">
          {!isOpen ? (
            <div className="card text-center">
              <p className="text-gray-600 mb-2">{electionData?.message || "Votação não disponível no momento."}</p>
              <p className="text-sm text-gray-400">Aguarde a abertura do próximo escrutínio.</p>
            </div>
          ) : (
            <div className="card">
              <h2 className="text-lg font-semibold mb-1">Identificação</h2>
              <p className="text-sm text-gray-500 mb-4">Informe seu CPF para receber a cédula.</p>

              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                <div className="mb-4">
                  <label className="label" htmlFor="cpf">CPF</label>
                  <input
                    id="cpf"
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    className="input text-lg tracking-widest"
                    placeholder="000.000.000-00"
                    value={cpfValue}
                    onChange={handleCpfChange}
                    aria-describedby={errors.cpf || serverError ? "cpf-error" : undefined}
                    aria-invalid={!!(errors.cpf || serverError)}
                  />
                  {(errors.cpf || serverError) && (
                    <p id="cpf-error" className="error-msg" role="alert">
                      {errors.cpf?.message || serverError}
                    </p>
                  )}
                </div>

                <button type="submit" className="btn-primary w-full text-base">
                  Continuar
                </button>
              </form>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
