import { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, CheckCircle, AlertTriangle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { QueryMetadata } from '../types'

interface ResponseCardProps {
  resposta: string
  resumo?: string
  fontes: string[]
  metadata: QueryMetadata
  disclaimer?: string
  sugestoes_followup?: string[]
  onFollowUp?: (query: string) => void
}

export function ResponseCard({
  resposta, resumo, fontes, metadata, disclaimer, sugestoes_followup, onFollowUp
}: ResponseCardProps) {
  const [detalhesAbertos, setDetalhesAbertos] = useState(true)

  const dadosCompletos = metadata.dados_completos
  const totalBanco = metadata.total_no_banco
  const numResultados = metadata.num_resultados

  return (
    <div className="mt-8">
      {/* Disclaimer */}
      {disclaimer && (
        <div className="flex items-start gap-2 px-3 py-2.5 mb-4 border border-caution-200 bg-caution-50 rounded-md text-small text-caution-700">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>{disclaimer}</span>
        </div>
      )}

      {/* Summary */}
      {resumo && (
        <div className="px-4 py-3 border-l-2 border-brand-400 bg-brand-50 rounded-r-md mb-4">
          <p className="text-body font-medium text-brand-800 leading-relaxed">{resumo}</p>
        </div>
      )}

      {/* Completeness indicator */}
      {totalBanco != null && totalBanco > 0 && (
        <div className="mb-4">
          {dadosCompletos ? (
            <span className="inline-flex items-center gap-1.5 text-caption px-2.5 py-1 text-positive-700 border border-positive-100 bg-positive-50 rounded-md">
              <CheckCircle size={12} />
              {numResultados} de {totalBanco} registros — dados completos
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-caption px-2.5 py-1 text-caution-700 border border-caution-200 bg-caution-50 rounded-md">
              <AlertTriangle size={12} />
              Exibindo {numResultados} de {totalBanco.toLocaleString('pt-BR')} registros (amostra)
            </span>
          )}
        </div>
      )}

      {/* Detail toggle */}
      <button
        onClick={() => setDetalhesAbertos(!detalhesAbertos)}
        className="flex items-center gap-1.5 text-caption text-brand-400 hover:text-brand-600 mb-3 transition-colors"
      >
        {detalhesAbertos ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {detalhesAbertos ? 'Ocultar análise completa' : 'Ver análise completa'}
      </button>

      {/* Response body */}
      {detalhesAbertos && (
        <div className="prose-response pb-4">
          <ReactMarkdown>{resposta}</ReactMarkdown>
        </div>
      )}

      {/* Follow-up suggestions */}
      {sugestoes_followup && sugestoes_followup.length > 0 && onFollowUp && (
        <div className="py-4 border-t border-surface-200">
          <p className="text-caption text-brand-400 mb-2.5">Perguntas relacionadas</p>
          <div className="flex flex-col gap-1.5">
            {sugestoes_followup.map((sugestao, i) => (
              <button
                key={i}
                onClick={() => onFollowUp(sugestao)}
                className="text-left text-small text-brand-600 hover:text-brand-800 hover:bg-brand-50
                           px-3 py-2 rounded-md transition-colors w-full"
              >
                <span className="mr-1.5 text-brand-300">&rarr;</span>
                {sugestao}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      <div className="py-3 border-t border-surface-200 flex flex-wrap gap-2">
        {fontes.map((fonte, i) => (
          <a
            key={i}
            href={fonte}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-caption px-2.5 py-1
                       border border-surface-200 rounded-md
                       text-brand-500 hover:text-brand-700 hover:border-brand-300 transition-colors"
          >
            <ExternalLink size={12} />
            {fonte.includes('camara') ? 'Câmara dos Deputados' : 'Portal da Transparência'}
          </a>
        ))}
      </div>

      {/* Metadata */}
      <div className="text-caption text-brand-300 flex flex-wrap gap-x-3 pt-1">
        <span>{(metadata.latencia_ms / 1000).toFixed(1)}s</span>
        <span>{metadata.modo}</span>
        <span>{metadata.num_resultados} registros</span>
      </div>
    </div>
  )
}
