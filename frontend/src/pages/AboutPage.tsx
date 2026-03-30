import { ExternalLink, AlertTriangle } from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="max-w-content mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-title text-brand-900 mb-2">Sobre o Fiscalia</h1>
        <p className="text-body text-brand-500 mx-auto max-w-[520px]">
          Uma plataforma aberta para consultar emendas parlamentares
          brasileiras em linguagem natural.
        </p>
      </div>

      <div className="space-y-10">
        {/* O projeto */}
        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-caption font-medium uppercase tracking-wider text-accent-500 mb-3">
            O projeto
          </h2>
          <p className="text-body text-brand-700 leading-relaxed">
            O Fiscalia permite consultar dados sobre emendas parlamentares
            federais em linguagem natural, recebendo respostas fundamentadas com
            citações verificáveis de fontes governamentais. É uma iniciativa
            acadêmica sem fins lucrativos.
          </p>
        </section>

        {/* Arquitetura */}
        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-caption font-medium uppercase tracking-wider text-accent-500 mb-3">
            Arquitetura
          </h2>
          <p className="text-body text-brand-700 leading-relaxed mb-5">
            O sistema utiliza uma arquitetura RAG (Retrieval-Augmented Generation) híbrida:
          </p>
          <div className="space-y-4">
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono font-medium text-accent-500 mt-0.5 shrink-0 w-5">01</span>
              <div>
                <span className="text-small font-semibold text-brand-800">Text-to-SQL</span>
                <span className="text-small text-brand-500"> — para consultas estruturadas (autor, ano, UF)</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono font-medium text-accent-500 mt-0.5 shrink-0 w-5">02</span>
              <div>
                <span className="text-small font-semibold text-brand-800">Busca vetorial semântica</span>
                <span className="text-small text-brand-500"> — para termos que exigem interpretação</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono font-medium text-accent-500 mt-0.5 shrink-0 w-5">03</span>
              <div>
                <span className="text-small font-semibold text-brand-800">LLM (Claude)</span>
                <span className="text-small text-brand-500"> — para síntese de respostas acessíveis</span>
              </div>
            </div>
          </div>
        </section>

        {/* Fontes */}
        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-caption font-medium uppercase tracking-wider text-accent-500 mb-3">
            Fontes de dados
          </h2>
          <div className="space-y-2.5">
            <a
              href="https://portaldatransparencia.gov.br"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-body text-brand-600 hover:text-brand-800 transition-colors group"
            >
              <ExternalLink size={14} className="text-brand-400 group-hover:text-brand-600" />
              Portal da Transparência (CGU)
            </a>
            <a
              href="https://dadosabertos.camara.leg.br"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-body text-brand-600 hover:text-brand-800 transition-colors group"
            >
              <ExternalLink size={14} className="text-brand-400 group-hover:text-brand-600" />
              Câmara dos Deputados — Dados Abertos
            </a>
          </div>
        </section>

        {/* Disclaimer */}
        <div className="flex items-start gap-2.5 text-small text-brand-500 px-2">
          <AlertTriangle size={14} className="text-caution-500 mt-0.5 shrink-0" />
          <p className="leading-relaxed">
            As respostas são geradas por inteligência artificial e podem conter
            imprecisões. Sempre verifique as informações nas fontes oficiais indicadas.
          </p>
        </div>
      </div>
    </div>
  )
}
