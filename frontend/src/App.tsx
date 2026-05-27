import { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { api } from "./lib/api";

export default function App() {
  useEffect(() => {
    // Garante que o cookie csrftoken seja setado antes de qualquer POST autenticado.
    api.get("/csrf").catch(() => {});
  }, []);

  return <RouterProvider router={router} />;
}
