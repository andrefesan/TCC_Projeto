import { ExternalLink } from 'lucide-react'
import type { QueryMetadata } from '../types'

interface ResponseCardProps {
  resposta: string
  fontes: string[]
  metadata: QueryMetadata
}

export function ResponseCard({ resposta, fontes, metadata }: ResponseCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <div className="prose max-w-none">
        <p className="text-gray-800 leading-relaxed whitespace-pre-line">
          {resposta}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {fontes.map((fonte, i) => (
          <a
            key={i}
            href={fonte}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm px-3 py-1
                       bg-success-50 text-success-500 rounded-full
                       hover:bg-green-100 transition"
          >
            <ExternalLink size={14} />
            {fonte.includes('camara') ? 'Câmara dos Deputados' : 'Portal da Transparência'}
          </a>
        ))}
      </div>

      <div className="mt-3 text-xs text-gray-400">
        Respondido em {(metadata.latencia_ms / 1000).toFixed(1)}s |
        Modo: {metadata.modo} |
        {metadata.num_resultados} registros
      </div>
    </div>
  )
}
