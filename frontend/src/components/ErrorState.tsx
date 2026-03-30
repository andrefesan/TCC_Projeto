import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message?: string
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="mt-8 border border-caution-200 bg-caution-50 rounded-md p-5">
      <div className="flex items-start gap-3">
        <AlertTriangle size={18} className="text-caution-600 mt-0.5 shrink-0" />
        <div>
          <h3 className="text-body font-semibold text-brand-900 mb-1.5">
            Dados insuficientes para esta consulta
          </h3>
          <p className="text-small text-brand-600 mb-4 leading-relaxed">
            {message || 'Os dados disponíveis não são suficientes para gerar uma resposta precisa.'}
          </p>
          <p className="text-caption font-medium text-brand-500 mb-2">Sugestões:</p>
          <ul className="text-small text-brand-500 space-y-1 ml-4 list-disc">
            <li>Especifique um parlamentar, estado ou ano</li>
            <li>Use uma consulta mais objetiva (ex: "emendas do deputado X em 2024")</li>
            <li>
              Consulte o{' '}
              <a
                href="https://portaldatransparencia.gov.br"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-600 underline underline-offset-2 hover:text-brand-800"
              >
                Portal da Transparência
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
