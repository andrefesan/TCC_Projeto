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
      {/* ── Landing ── */}
      {!hasResults && !isPending && !isError && (
        <>
          {/* Hero with gradient */}
          <section className="hero-gradient">
            <div className="max-w-wide mx-auto px-4 sm:px-6 lg:px-8 pt-14 pb-12 sm:pt-20 sm:pb-16 text-center">
              <div className="flex justify-center mb-5">
                <span className="inline-flex items-center gap-1.5 text-caption font-medium px-3 py-1 rounded-full border border-brand-200/60 bg-white/70 text-brand-600 backdrop-blur-sm">
                  <BookOpen size={12} />
                  Iniciativa acadêmica sem fins lucrativos
                </span>
              </div>

              <h1 className="text-display text-brand-950 mx-auto max-w-[640px]">
                Consulte emendas parlamentares em linguagem natural
              </h1>
              <p className="text-body text-brand-500 mt-5 mx-auto max-w-[520px] leading-relaxed">
                Faça perguntas sobre os R$ 200+ bilhões em emendas parlamentares federais
                de 2020 a 2024. Respostas fundamentadas com fontes oficiais do governo.
              </p>

              <div className="mt-8 max-w-[640px] mx-auto">
                <SearchBar onSearch={handleSearch} isLoading={isPending} variant="hero" />
              </div>
            </div>
          </section>

          {/* How it works */}
          <section className="bg-white border-t border-surface-200">
            <div className="max-w-wide mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-16">
              <h2 className="text-heading text-brand-900 mb-10 text-center">Como funciona</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-10">
                <div className="surface-card p-5 sm:p-6">
                  <div className="text-caption font-mono font-medium text-accent-500 mb-2">01</div>
                  <h3 className="text-body font-semibold text-brand-800 mb-1.5">
                    Pergunte em linguagem natural
                  </h3>
                  <p className="text-small text-brand-500 leading-relaxed">
                    Escreva sua dúvida como faria a um especialista. O sistema entende contexto, nomes e temas.
                  </p>
                </div>
                <div className="surface-card p-5 sm:p-6">
                  <div className="text-caption font-mono font-medium text-accent-500 mb-2">02</div>
                  <h3 className="text-body font-semibold text-brand-800 mb-1.5">
                    Busca nos dados oficiais
                  </h3>
                  <p className="text-small text-brand-500 leading-relaxed">
                    O sistema combina busca estruturada (SQL) e semântica em 32.787 emendas de 27 estados.
                  </p>
                </div>
                <div className="surface-card p-5 sm:p-6">
                  <div className="text-caption font-mono font-medium text-accent-500 mb-2">03</div>
                  <h3 className="text-body font-semibold text-brand-800 mb-1.5">
                    Resposta com fontes
                  </h3>
                  <p className="text-small text-brand-500 leading-relaxed">
                    Receba uma resposta clara com citações verificáveis do Portal da Transparência e Câmara.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Stats */}
          <section className="bg-brand-950">
            <div className="max-w-wide mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8 text-center">
              <div>
                <div className="text-title font-bold text-white font-mono">32.787</div>
                <div className="text-caption text-brand-400 mt-1">emendas indexadas</div>
              </div>
              <div>
                <div className="text-title font-bold text-white font-mono">27</div>
                <div className="text-caption text-brand-400 mt-1">unidades federativas</div>
              </div>
              <div>
                <div className="text-title font-bold text-white font-mono">2020–2024</div>
                <div className="text-caption text-brand-400 mt-1">período coberto</div>
              </div>
              <div>
                <div className="text-title font-bold text-accent-400 font-mono">100%</div>
                <div className="text-caption text-brand-400 mt-1">dados abertos</div>
              </div>
            </div>
          </section>
        </>
      )}

      {/* ── Loading ── */}
      {isPending && (
        <div className="max-w-content mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <SearchBar onSearch={handleSearch} isLoading={isPending} variant="compact" />
          <LoadingState />
        </div>
      )}

      {/* ── Error ── */}
      {isError && (
        <div className="max-w-content mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <SearchBar onSearch={handleSearch} isLoading={isPending} variant="compact" />
          <ErrorState message={error?.message} />
        </div>
      )}

      {/* ── Results ── */}
      {hasResults && (
        <div className="max-w-content mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
