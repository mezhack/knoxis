import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";

const schema = z.object({
  name: z.string().min(2, "Nome obrigatório"),
  email: z.string().email("Email inválido"),
  password: z.string().min(12, "Senha deve ter ao menos 12 caracteres"),
  org_name: z.string().min(3, "Nome da organização obrigatório"),
  org_slug: z
    .string()
    .min(3, "Identificador obrigatório")
    .regex(/^[a-z0-9-]+$/, "Apenas letras minúsculas, números e hífens"),
  org_city: z.string().optional(),
  org_state: z.string().max(2).optional(),
});

type FormData = z.infer<typeof schema>;

export default function SignupPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState("");

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const signup = useMutation({
    mutationFn: (data: FormData) =>
      api.post("/admin/auth/signup", {
        name: data.name,
        email: data.email,
        password: data.password,
        organization: {
          name: data.org_name,
          slug: data.org_slug,
          city: data.org_city || null,
          state: data.org_state || null,
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["me"] });
      navigate("/");
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setServerError(err.message);
      }
    },
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-700">Knoxis</h1>
          <p className="text-gray-500 mt-1">Criar conta</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit((d) => signup.mutate(d))} noValidate>
            <h2 className="text-lg font-semibold mb-4">Seus dados</h2>

            <div className="mb-4">
              <label className="label">Nome completo</label>
              <input type="text" className="input" {...register("name")} />
              {errors.name && <p className="error-msg">{errors.name.message}</p>}
            </div>
            <div className="mb-4">
              <label className="label">Email</label>
              <input type="email" className="input" {...register("email")} />
              {errors.email && <p className="error-msg">{errors.email.message}</p>}
            </div>
            <div className="mb-6">
              <label className="label">Senha (mín. 12 caracteres)</label>
              <input type="password" className="input" {...register("password")} />
              {errors.password && <p className="error-msg">{errors.password.message}</p>}
            </div>

            <h2 className="text-lg font-semibold mb-4 border-t pt-4">Sua organização</h2>

            <div className="mb-4">
              <label className="label">Nome da igreja</label>
              <input type="text" className="input" placeholder="Igreja Presbiteriana de..." {...register("org_name")} />
              {errors.org_name && <p className="error-msg">{errors.org_name.message}</p>}
            </div>
            <div className="mb-4">
              <label className="label">Identificador único (slug)</label>
              <input type="text" className="input" placeholder="ipb-cidade" {...register("org_slug")} />
              <p className="text-xs text-gray-400 mt-1">Usado na URL pública da eleição. Apenas letras minúsculas e hífens.</p>
              {errors.org_slug && <p className="error-msg">{errors.org_slug.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div>
                <label className="label">Cidade</label>
                <input type="text" className="input" {...register("org_city")} />
              </div>
              <div>
                <label className="label">Estado (UF)</label>
                <input type="text" className="input" maxLength={2} placeholder="SP" {...register("org_state")} />
              </div>
            </div>

            {serverError && <p className="error-msg mb-4" role="alert">{serverError}</p>}

            <button type="submit" className="btn-primary w-full" disabled={signup.isPending}>
              {signup.isPending ? "Criando conta..." : "Criar conta"}
            </button>
          </form>

          <p className="text-sm text-center mt-4 text-gray-600">
            Já tem conta? <Link to="/login">Entrar</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
