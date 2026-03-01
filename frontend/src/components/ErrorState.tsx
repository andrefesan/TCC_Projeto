import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message?: string
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="text-center py-12">
      <AlertTriangle size={48} className="mx-auto text-warning-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-800 mb-2">
        Erro ao processar consulta
      </h3>
      <p className="text-gray-500 max-w-md mx-auto mb-4">
        {message || 'Não foi possível responder com confiança a esta consulta. Tente reformular sua pergunta.'}
      </p>
      <a
        href="https://portaldatransparencia.gov.br"
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary-600 hover:underline text-sm"
      >
        Consultar diretamente o Portal da Transparência
      </a>
    </div>
  )
}
