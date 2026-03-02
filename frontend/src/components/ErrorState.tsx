import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message?: string
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="bg-warning-50 border border-warning-200 rounded-lg p-6 mt-6">
      <div className="flex items-start gap-4">
        <AlertTriangle size={28} className="text-warning-500 mt-0.5 shrink-0" />
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Insuficiência de dados
          </h3>
          <p className="text-gray-600 mb-4 leading-relaxed">
            {message || 'Não foi possível responder com confiança a esta consulta. Os dados disponíveis na base não são suficientes para gerar uma resposta precisa.'}
          </p>
          <div className="text-sm text-gray-500 space-y-1">
            <p className="font-medium">Sugestões:</p>
            <ul className="list-disc list-inside ml-2 space-y-0.5">
              <li>Reformule a pergunta especificando um parlamentar, estado ou ano</li>
              <li>Tente uma consulta mais objetiva (ex: &ldquo;emendas do deputado X em 2024&rdquo;)</li>
              <li>
                Consulte diretamente o{' '}
                <a
                  href="https://portaldatransparencia.gov.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  Portal da Transparência
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
