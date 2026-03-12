import { ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { QueryMetadata } from '../types'

interface ResponseCardProps {
  resposta: string
  fontes: string[]
  metadata: QueryMetadata
  disclaimer?: string
}

export function ResponseCard({ resposta, fontes, metadata, disclaimer }: ResponseCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 mt-6 overflow-hidden">
      {disclaimer && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-sm text-amber-800">
          <span className="font-medium">⚠️ Aviso de limitação: </span>
          {disclaimer}
        </div>
      )}
      <div className="prose prose-slate max-w-none break-words prose-headings:text-lg prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2 prose-p:my-2 prose-li:my-0.5">
        <ReactMarkdown>{resposta}</ReactMarkdown>
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

      <div className="mt-3 text-xs text-gray-400 flex flex-wrap gap-x-1">
        <span>Respondido em {(metadata.latencia_ms / 1000).toFixed(1)}s</span>
        <span>| Modo: {metadata.modo}</span>
        <span>| {metadata.num_resultados} registros</span>
      </div>
    </div>
  )
}
