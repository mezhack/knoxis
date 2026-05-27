import { Navigate } from "react-router-dom";
import { useAuth } from "../../../hooks/useAuth";

interface Props {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: Props) {
  const { data, isLoading, isError } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  if (isError || !data?.user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
