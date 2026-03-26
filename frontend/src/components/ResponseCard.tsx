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
    <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 mt-6 overflow-hidden">
      {disclaimer && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-sm text-amber-800">
          <span className="font-medium">⚠️ Aviso de limitação: </span>
          {disclaimer}
        </div>
      )}

      {/* Banner de resumo */}
      {resumo && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-blue-900 text-base font-medium leading-relaxed">
            {resumo}
          </p>
        </div>
      )}

      {/* Indicador de completude */}
      {totalBanco != null && totalBanco > 0 && (
        <div className="mb-4">
          {dadosCompletos ? (
            <span className="inline-flex items-center gap-1.5 text-sm px-3 py-1 bg-green-50 text-green-700 rounded-full border border-green-200">
              <CheckCircle size={14} />
              {numResultados} de {totalBanco} registros (dados completos)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-sm px-3 py-1 bg-amber-50 text-amber-700 rounded-full border border-amber-200">
              <AlertTriangle size={14} />
              {numResultados} de {totalBanco.toLocaleString('pt-BR')} registros (amostra por maior valor)
            </span>
          )}
        </div>
      )}

      {/* Detalhes colapsáveis */}
      <button
        onClick={() => setDetalhesAbertos(!detalhesAbertos)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2 transition"
      >
        {detalhesAbertos ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        {detalhesAbertos ? 'Ocultar detalhes' : 'Mostrar detalhes'}
      </button>

      {detalhesAbertos && (
        <div className="prose prose-slate max-w-none break-words prose-headings:text-lg prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2 prose-p:my-2 prose-li:my-0.5">
          <ReactMarkdown>{resposta}</ReactMarkdown>
        </div>
      )}

      {/* Sugestões de follow-up */}
      {sugestoes_followup && sugestoes_followup.length > 0 && onFollowUp && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Perguntas relacionadas:</p>
          <div className="flex flex-wrap gap-2">
            {sugestoes_followup.map((sugestao, i) => (
              <button
                key={i}
                onClick={() => onFollowUp(sugestao)}
                className="text-xs px-3 py-1.5 bg-primary-50 text-primary-600
                           rounded-full hover:bg-primary-100 transition
                           border border-primary-200"
              >
                {sugestao}
              </button>
            ))}
          </div>
        </div>
      )}

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
