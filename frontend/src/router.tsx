import { createBrowserRouter } from "react-router-dom";
import AdminLayout from "./modules/admin/components/AdminLayout";
import ProtectedRoute from "./modules/admin/components/ProtectedRoute";
import LoginPage from "./modules/admin/pages/LoginPage";
import SignupPage from "./modules/admin/pages/SignupPage";
import ElectionListPage from "./modules/admin/pages/ElectionListPage";
import ElectionFormPage from "./modules/admin/pages/ElectionFormPage";
import ElectionDashboardPage from "./modules/admin/pages/ElectionDashboardPage";
import EscrutinioParciaisPage from "./modules/admin/pages/EscrutinioParciaisPage";
import EscrutinioResultadoPage from "./modules/admin/pages/EscrutinioResultadoPage";
import RelatorioImpressoPage from "./modules/admin/pages/RelatorioImpressoPage";
import NotFoundPage from "./modules/admin/pages/NotFoundPage";
import ElectionEntryPage from "./modules/voter/pages/ElectionEntryPage";
import BallotPage from "./modules/voter/pages/BallotPage";
import ConfirmationPage from "./modules/voter/pages/ConfirmationPage";

export const router = createBrowserRouter([
  // Admin routes
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/cadastro",
    element: <SignupPage />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <ElectionListPage /> },
      { path: "eleicoes/nova", element: <ElectionFormPage /> },
      { path: "eleicoes/:id", element: <ElectionDashboardPage /> },
      { path: "eleicoes/:id/editar", element: <ElectionFormPage /> },
      { path: "escrutinios/:id/resultado", element: <EscrutinioResultadoPage /> },
      { path: "eleicoes/:id/relatorios", element: <RelatorioImpressoPage /> },
    ],
  },
  {
    path: "/escrutinios/:id/parciais",
    element: (
      <ProtectedRoute>
        <EscrutinioParciaisPage />
      </ProtectedRoute>
    ),
  },
  // Voter routes (public)
  {
    path: "/votar/:slug",
    element: <ElectionEntryPage />,
  },
  {
    path: "/votar/:slug/cedula",
    element: <BallotPage />,
  },
  {
    path: "/votar/confirmacao",
    element: <ConfirmationPage />,
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
