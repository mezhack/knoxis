export default function ConfirmationPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="card max-w-sm w-full text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Voto registrado!</h1>
        <p className="text-gray-600 text-sm">
          Seu voto foi registrado com sucesso. Você pode fechar esta página.
        </p>
        <p className="text-xs text-gray-400 mt-4">
          Se houver um próximo escrutínio, você receberá instruções do organizador.
        </p>
      </div>
    </div>
  );
}
