import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../../../lib/api";

const schema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(1, "Senha obrigatória"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const login = useMutation({
    mutationFn: (data: FormData) => api.post("/admin/auth/login", data),
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-brand-700">Knoxis</h1>
          <p className="text-gray-500 mt-1">Votação segura para igrejas</p>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold mb-6">Entrar</h2>

          <form onSubmit={handleSubmit((d) => login.mutate(d))} noValidate>
            <div className="mb-4">
              <label className="label" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                className="input"
                autoComplete="email"
                {...register("email")}
                aria-describedby={errors.email ? "email-error" : undefined}
                aria-invalid={!!errors.email}
              />
              {errors.email && (
                <p id="email-error" className="error-msg" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="mb-6">
              <label className="label" htmlFor="password">Senha</label>
              <input
                id="password"
                type="password"
                className="input"
                autoComplete="current-password"
                {...register("password")}
                aria-describedby={errors.password ? "password-error" : undefined}
                aria-invalid={!!errors.password}
              />
              {errors.password && (
                <p id="password-error" className="error-msg" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            {serverError && (
              <p className="error-msg mb-4" role="alert">{serverError}</p>
            )}

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={login.isPending}
            >
              {login.isPending ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <p className="text-sm text-center mt-4 text-gray-600">
            Não tem conta?{" "}
            <Link to="/cadastro">Criar conta</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
