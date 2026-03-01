import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { EmendaData } from '../types'

interface DataTableProps {
  data: EmendaData[]
}

type SortField = 'nome_autor' | 'partido' | 'uf' | 'funcao_nome' | 'valor_empenhado' | 'valor_pago' | 'ano'

function formatarReal(valor: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor)
}

export function DataTable({ data }: DataTableProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [sortField, setSortField] = useState<SortField>('valor_empenhado')
  const [sortAsc, setSortAsc] = useState(false)
  const [page, setPage] = useState(0)
  const pageSize = 20

  if (!data.length) return null

  const sorted = [...data].sort((a, b) => {
    const aVal = a[sortField] ?? ''
    const bVal = b[sortField] ?? ''
    const cmp = typeof aVal === 'number' && typeof bVal === 'number'
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
    <div className="mt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-sm text-primary-600 hover:text-primary-700 font-medium"
      >
        {isExpanded ? 'Ocultar' : 'Ver'} dados brutos ({data.length} registros)
      </button>

      {isExpanded && (
        <div className="mt-3 overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {([
                  ['nome_autor', 'Parlamentar'],
                  ['partido', 'Partido'],
                  ['uf', 'UF'],
                  ['funcao_nome', 'Função'],
                  ['valor_empenhado', 'Empenhado'],
                  ['valor_pago', 'Pago'],
                  ['ano', 'Ano'],
                ] as [SortField, string][]).map(([field, label]) => (
                  <th
                    key={field}
                    onClick={() => handleSort(field)}
                    className="px-3 py-2 text-left cursor-pointer hover:bg-gray-100
                               select-none whitespace-nowrap"
                  >
                    <span className="inline-flex items-center gap-1">
                      {label} <SortIcon field={field} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {paged.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{row.nome_autor || '-'}</td>
                  <td className="px-3 py-2">{row.partido || '-'}</td>
                  <td className="px-3 py-2">{row.uf || '-'}</td>
                  <td className="px-3 py-2">{row.funcao_nome || '-'}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {formatarReal(row.valor_empenhado)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {formatarReal(row.valor_pago)}
                  </td>
                  <td className="px-3 py-2 text-center">{row.ano}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-3 py-2 bg-gray-50 text-xs">
              <span>Página {page + 1} de {totalPages}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-2 py-1 border rounded disabled:opacity-50"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-2 py-1 border rounded disabled:opacity-50"
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
