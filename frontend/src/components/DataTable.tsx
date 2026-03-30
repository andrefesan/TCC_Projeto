import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import type { EmendaData } from '../types'

interface DataTableProps {
  data: EmendaData[]
  defaultExpanded?: boolean
}

type SortField = 'nome_autor' | 'partido' | 'uf' | 'funcao_nome' | 'valor_empenhado' | 'valor_pago' | 'ano'

function formatarReal(valor: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor)
}

const COLUMNS: [SortField, string][] = [
  ['nome_autor', 'Parlamentar'],
  ['partido', 'Partido'],
  ['uf', 'UF'],
  ['funcao_nome', 'Função'],
  ['valor_empenhado', 'Empenhado'],
  ['valor_pago', 'Pago'],
  ['ano', 'Ano'],
]

export function DataTable({ data, defaultExpanded = false }: DataTableProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [sortField, setSortField] = useState<SortField>('valor_empenhado')
  const [sortAsc, setSortAsc] = useState(false)
  const [page, setPage] = useState(0)
  const pageSize = 20

  if (!data.length) return null

  const sorted = [...data].sort((a, b) => {
    const aVal = a[sortField] ?? ''
    const bVal = b[sortField] ?? ''
    const cmp =
      typeof aVal === 'number' && typeof bVal === 'number'
        ? aVal - bVal
        : String(aVal).localeCompare(String(bVal))
    return sortAsc ? cmp : -cmp
  })

  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.ceil(sorted.length / pageSize)

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (field !== sortField) return null
    return sortAsc ? <ChevronUp size={14} /> : <ChevronDown size={14} />
  }

  return (
    <div className="mt-6 border-t border-surface-200 pt-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-small text-brand-500 hover:text-brand-700 transition-colors"
      >
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        <span className="font-medium">
          {isExpanded ? 'Ocultar' : 'Ver'} dados tabulares
        </span>
        <span className="text-caption text-brand-400">
          ({data.length} registros)
        </span>
      </button>

      {isExpanded && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-small">
            <thead>
              <tr className="border-b border-surface-200">
                {COLUMNS.map(([field, label]) => (
                  <th
                    key={field}
                    onClick={() => handleSort(field)}
                    className={clsx(
                      'px-3 py-2.5 text-left text-caption font-medium uppercase tracking-wider cursor-pointer',
                      'select-none whitespace-nowrap transition-colors',
                      field === sortField
                        ? 'text-brand-800'
                        : 'text-brand-400 hover:text-brand-600'
                    )}
                  >
                    <span className="inline-flex items-center gap-1">
                      {label} <SortIcon field={field} />
                    </span>
                  </th>
                ))}
                <th className="px-3 py-2.5 text-left text-caption font-medium uppercase tracking-wider text-brand-400">
                  Fonte
                </th>
              </tr>
            </thead>
            <tbody>
              {paged.map((row, idx) => (
                <tr
                  key={row.id}
                  className={clsx(
                    'border-b border-surface-100 hover:bg-brand-50/50 transition-colors',
                    idx % 2 === 0 ? 'bg-white' : 'bg-surface-50'
                  )}
                >
                  <td className="px-3 py-2.5">
                    {row.parlamentar_url ? (
                      <a
                        href={row.parlamentar_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-600 hover:text-brand-800 underline underline-offset-2"
                      >
                        {row.nome_autor || '—'}
                      </a>
                    ) : (
                      <span className="text-brand-800">{row.nome_autor || '—'}</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-brand-600">{row.partido || '—'}</td>
                  <td className="px-3 py-2.5 text-brand-600">{row.uf || '—'}</td>
                  <td className="px-3 py-2.5 text-brand-600">{row.funcao_nome || '—'}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-brand-800">
                    {formatarReal(row.valor_empenhado)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-brand-800">
                    {formatarReal(row.valor_pago)}
                  </td>
                  <td className="px-3 py-2.5 text-center font-mono text-brand-600">
                    {row.ano}
                  </td>
                  <td className="px-3 py-2.5">
                    {row.source_url && (
                      <a
                        href={row.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-400 hover:text-brand-700 transition-colors"
                      >
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="flex items-center justify-between py-3 border-t border-surface-200 text-caption">
              <span className="text-brand-400">
                Página {page + 1} de {totalPages}
              </span>
              <div className="flex gap-1.5">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-3 py-1.5 border border-surface-200 rounded-md text-brand-600
                             hover:bg-brand-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-3 py-1.5 border border-surface-200 rounded-md text-brand-600
                             hover:bg-brand-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Próximo
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
