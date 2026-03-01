import { SearchBar } from '../components/SearchBar'
import { ResponseCard } from '../components/ResponseCard'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { LoadingState } from '../components/LoadingState'
import { ErrorState } from '../components/ErrorState'
import { useConsulta } from '../hooks/useQuery'

export default function HomePage() {
  const { mutate, data, isPending, isError, error } = useConsulta()

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
          Transparência Fiscal
        </h1>
        <p className="text-center text-gray-500 mb-8">
          Consulta inteligente de emendas parlamentares federais
        </p>
        <SearchBar onSearch={(q) => mutate(q)} isLoading={isPending} />
      </div>

      {isPending && <LoadingState />}

      {isError && (
        <ErrorState message={error?.message} />
      )}

      {data && !isPending && (
        <>
          <ResponseCard
            resposta={data.resposta}
            fontes={data.fontes}
            metadata={data.metadata}
          />
          <DataTable data={data.dados} />
        </>
      )}

      {!data && !isPending && !isError && <EmptyState />}
    </div>
  )
}
