import { BookOpen } from 'lucide-react'
import { SearchBar } from '../components/SearchBar'
import { ResponseCard } from '../components/ResponseCard'
import { DataTable } from '../components/DataTable'
import { LoadingState } from '../components/LoadingState'
import { ErrorState } from '../components/ErrorState'
import { useConsulta } from '../hooks/useQuery'

export default function HomePage() {
  const { mutate, data, isPending, isError, error } = useConsulta()

  const handleSearch = (q: string) => mutate(q)

  const hasResults = data && !isPending && !isError

  return (
    <div>
      {/* ── Landing (shown when no results) ── */}
      {!hasResults && !isPending && !isError && (
        <>
          {/* Hero */}
          <section className="max-w-content mx-auto px-4 sm:px-6 pt-16 pb-8 sm:pt-24 sm:pb-12">
            <div className="flex items-center gap-2 mb-6">
              <span className="inline-flex items-center gap-1.5 text-caption font-medium px-2.5 py-1 rounded-full border border-surface-200 text-brand-500">
                <BookOpen size={12} />
                Projeto acadêmico sem fins lucrativos
              </span>
            </div>

            <h1 className="text-display text-brand-950 max-w-[560px]">
              Consulte emendas parlamentares em linguagem natural
            </h1>
            <p className="text-body text-brand-500 mt-4 max-w-[480px] leading-relaxed">
              Faça perguntas sobre os R$ 200+ bilhões em emendas parlamentares federais
              de 2020 a 2024. Respostas fundamentadas com fontes oficiais do governo.
            </p>
          </section>

          {/* Search */}
          <section className="max-w-content mx-auto px-4 sm:px-6">
            <SearchBar onSearch={handleSearch} isLoading={isPending} variant="hero" />
          </section>

          {/* How it works */}
          <section className="max-w-wide mx-auto px-4 sm:px-6 pt-20 pb-12">
            <h2 className="text-heading text-brand-900 mb-8">Como funciona</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
              <div>
                <div className="text-caption font-mono font-medium text-brand-400 mb-2">01</div>
                <h3 className="text-body font-semibold text-brand-800 mb-1">
                  Pergunte em linguagem natural
                </h3>
                <p className="text-small text-brand-500">
                  Escreva sua dúvida como faria a um especialista. O sistema entende contexto, nomes e temas.
                </p>
              </div>
              <div>
                <div className="text-caption font-mono font-medium text-brand-400 mb-2">02</div>
                <h3 className="text-body font-semibold text-brand-800 mb-1">
                  Busca nos dados oficiais
                </h3>
                <p className="text-small text-brand-500">
                  O sistema combina busca estruturada (SQL) e semântica em 32.787 emendas de 27 estados.
                </p>
              </div>
              <div>
                <div className="text-caption font-mono font-medium text-brand-400 mb-2">03</div>
                <h3 className="text-body font-semibold text-brand-800 mb-1">
                  Resposta com fontes
                </h3>
                <p className="text-small text-brand-500">
                  Receba uma resposta clara com citações verificáveis do Portal da Transparência e Câmara dos Deputados.
                </p>
              </div>
            </div>
          </section>

          {/* Stats */}
          <section className="border-y border-surface-200 bg-white">
            <div className="max-w-wide mx-auto px-4 sm:px-6 py-8 flex flex-wrap gap-x-12 gap-y-4">
              <div>
                <div className="text-title font-bold text-brand-900 font-mono">32.787</div>
                <div className="text-caption text-brand-500">emendas indexadas</div>
              </div>
              <div>
                <div className="text-title font-bold text-brand-900 font-mono">27</div>
                <div className="text-caption text-brand-500">unidades federativas</div>
              </div>
              <div>
                <div className="text-title font-bold text-brand-900 font-mono">2020–2024</div>
                <div className="text-caption text-brand-500">período coberto</div>
              </div>
              <div>
                <div className="text-title font-bold text-brand-900 font-mono">100%</div>
                <div className="text-caption text-brand-500">dados abertos</div>
              </div>
            </div>
          </section>
        </>
      )}

      {/* ── Loading ── */}
      {isPending && (
        <div className="max-w-content mx-auto px-4 sm:px-6 py-8">
          <SearchBar onSearch={handleSearch} isLoading={isPending} variant="compact" />
          <LoadingState />
        </div>
      )}

      {/* ── Error ── */}
      {isError && (
        <div className="max-w-content mx-auto px-4 sm:px-6 py-8">
          <SearchBar onSearch={handleSearch} isLoading={isPending} variant="compact" />
          <ErrorState message={error?.message} />
        </div>
      )}

      {/* ── Results ── */}
      {hasResults && (
        <div className="max-w-content mx-auto px-4 sm:px-6 py-8">
          <SearchBar onSearch={handleSearch} isLoading={isPending} variant="compact" />
          <ResponseCard
            resposta={data.resposta}
            resumo={data.resumo}
            fontes={data.fontes}
            metadata={data.metadata}
            disclaimer={data.disclaimer}
            sugestoes_followup={data.sugestoes_followup}
            onFollowUp={handleSearch}
          />
          <DataTable data={data.dados} />
        </div>
      )}
    </div>
  )
}
