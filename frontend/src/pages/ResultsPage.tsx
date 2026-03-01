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
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Explorar Emendas
      </h1>

      <FilterPanel filters={filters} onChange={setFilters} />

      <div className="mt-6">
        {isLoading && <LoadingState />}
        {isError && <ErrorState message="Erro ao buscar emendas." />}
        {data && (
          <>
            <p className="text-sm text-gray-500 mb-3">
              {data.total} emendas encontradas (página {data.page} de{' '}
              {Math.ceil(data.total / data.page_size)})
            </p>
            <DataTable data={data.items} />
          </>
        )}
        {!data && !isLoading && Object.keys(filters).length === 0 && (
          <p className="text-gray-400 text-center py-12">
            Selecione pelo menos um filtro para explorar emendas.
          </p>
        )}
      </div>
    </div>
  )
}
