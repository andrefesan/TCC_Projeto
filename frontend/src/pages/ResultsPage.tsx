import { useState } from 'react'
import { FilterPanel } from '../components/FilterPanel'
import { DataTable } from '../components/DataTable'
import { LoadingState } from '../components/LoadingState'
import { ErrorState } from '../components/ErrorState'
import { useEmendas } from '../hooks/useEmendas'

export default function ResultsPage() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const { data, isLoading, isError } = useEmendas(filters)

  return (
    <div className="max-w-wide mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-title text-brand-900">Explorar emendas</h1>
        <p className="text-small text-brand-500 mt-1">
          Navegue pelos dados brutos filtrando por ano, estado e partido.
        </p>
      </div>

      <FilterPanel filters={filters} onChange={setFilters} />

      <div className="mt-8">
        {isLoading && <LoadingState />}
        {isError && <ErrorState message="Erro ao buscar emendas." />}
        {data && (
          <>
            <p className="text-caption text-brand-400 mb-4">
              {data.total.toLocaleString('pt-BR')} emendas encontradas
              <span className="mx-1.5 text-brand-300">|</span>
              Página {data.page} de {Math.ceil(data.total / data.page_size)}
            </p>
            <DataTable data={data.items} defaultExpanded />
          </>
        )}
        {!data && !isLoading && Object.keys(filters).length === 0 && (
          <div className="py-16 text-center">
            <p className="text-body text-brand-400">
              Selecione ao menos um filtro para explorar os dados.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
