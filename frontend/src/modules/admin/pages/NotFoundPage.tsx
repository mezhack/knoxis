import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <h1 className="text-6xl font-bold text-gray-300">404</h1>
      <p className="mt-4 text-xl text-gray-700">Página não encontrada</p>
      <p className="mt-2 text-gray-500">
        O recurso que você buscou não existe ou não está disponível.
      </p>
      <Link to="/" className="btn-primary mt-8">
        Voltar ao início
      </Link>
    </div>
  );
}
