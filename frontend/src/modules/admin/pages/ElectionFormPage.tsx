import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";
import type { Election } from "../../../lib/types";
import { useState } from "react";

const schema = z
  .object({
    name: z.string().min(3, "Nome obrigatório"),
    description: z.string().optional(),
    scheduled_for: z.string().optional(),
    final_rule: z.enum(["manual", "max_count"]),
    max_escrutinios: z.number().int().min(1).optional().nullable(),
  })
  .refine(
    (d) => d.final_rule !== "max_count" || !!d.max_escrutinios,
    { message: "Defina o número máximo de escrutínios", path: ["max_escrutinios"] }
  );

type FormData = z.infer<typeof schema>;

export default function ElectionFormPage() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState("");

  const { data: election } = useQuery({
    queryKey: ["elections", id],
    queryFn: () => api.get<Election>(`/admin/elections/${id}`),
    enabled: isEdit,
  });

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    values: election
      ? {
          name: election.name,
          description: election.description ?? "",
          scheduled_for: election.scheduled_for ?? "",
          final_rule: election.final_rule,
          max_escrutinios: election.max_escrutinios ?? null,
        }
      : undefined,
  });

  const finalRule = watch("final_rule");

  const save = useMutation({
    mutationFn: (data: FormData) =>
      isEdit
        ? api.patch(`/admin/elections/${id}`, data)
        : api.post("/admin/elections", data),
    onSuccess: (result: any) => {
      qc.invalidateQueries({ queryKey: ["elections"] });
      navigate(`/eleicoes/${result.id ?? id}`);
    },
    onError: (err) => {
      if (err instanceof ApiError) setServerError(err.message);
    },
  });

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">{isEdit ? "Editar eleição" : "Nova eleição"}</h1>

      <div className="card">
        <form onSubmit={handleSubmit((d) => save.mutate(d))} noValidate>
          <div className="mb-4">
            <label className="label">Nome da eleição *</label>
            <input type="text" className="input" {...register("name")} />
            {errors.name && <p className="error-msg">{errors.name.message}</p>}
          </div>

          <div className="mb-4">
            <label className="label">Descrição</label>
            <textarea rows={3} className="input resize-none" {...register("description")} />
          </div>

          <div className="mb-4">
            <label className="label">Data prevista</label>
            <input type="date" className="input" {...register("scheduled_for")} />
          </div>

          <div className="mb-4">
            <label className="label">Regra do escrutínio final *</label>
            <select className="input" {...register("final_rule")}>
              <option value="max_count">Limitar a N escrutínios</option>
              <option value="manual">Marcar manualmente</option>
            </select>
          </div>

          {finalRule === "max_count" && (
            <div className="mb-4">
              <label className="label">Número máximo de escrutínios *</label>
              <input
                type="number"
                min={1}
                className="input"
                {...register("max_escrutinios", { valueAsNumber: true })}
              />
              {errors.max_escrutinios && <p className="error-msg">{errors.max_escrutinios.message}</p>}
            </div>
          )}

          {serverError && <p className="error-msg mb-4">{serverError}</p>}

          <div className="flex gap-3">
            <button type="submit" className="btn-primary" disabled={save.isPending}>
              {save.isPending ? "Salvando..." : "Salvar"}
            </button>
            <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
