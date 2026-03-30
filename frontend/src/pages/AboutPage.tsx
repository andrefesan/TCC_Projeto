import { ExternalLink, AlertTriangle } from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="max-w-content mx-auto px-4 sm:px-6 py-12">
      <h1 className="text-title text-brand-900 mb-2">Sobre o Fiscalia</h1>
      <p className="text-body text-brand-500 mb-12 max-w-[480px]">
        Uma plataforma aberta para consultar emendas parlamentares
        brasileiras em linguagem natural.
      </p>

      <div className="space-y-12">
        {/* O projeto */}
        <section>
          <h2 className="text-caption font-medium uppercase tracking-wider text-brand-400 mb-3">
            O projeto
          </h2>
          <p className="text-body text-brand-700 leading-relaxed max-w-[560px]">
            O Fiscalia permite consultar dados sobre emendas parlamentares
            federais em linguagem natural, recebendo respostas fundamentadas com
            citações verificáveis de fontes governamentais. É um projeto acadêmico
            sem fins lucrativos, desenvolvido como Trabalho de Conclusão de Curso
            em Sistemas de Informação.
          </p>
        </section>

        {/* Arquitetura */}
        <section>
          <h2 className="text-caption font-medium uppercase tracking-wider text-brand-400 mb-3">
            Arquitetura
          </h2>
          <p className="text-body text-brand-700 leading-relaxed mb-4 max-w-[560px]">
            O sistema utiliza uma arquitetura RAG (Retrieval-Augmented Generation) híbrida:
          </p>
          <div className="space-y-3 max-w-[560px]">
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono text-brand-400 mt-0.5 shrink-0">01</span>
              <div>
                <span className="text-small font-semibold text-brand-800">Text-to-SQL</span>
                <span className="text-small text-brand-500"> — para consultas estruturadas (autor, ano, UF)</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono text-brand-400 mt-0.5 shrink-0">02</span>
              <div>
                <span className="text-small font-semibold text-brand-800">Busca vetorial semântica</span>
                <span className="text-small text-brand-500"> — para termos que exigem interpretação</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-caption font-mono text-brand-400 mt-0.5 shrink-0">03</span>
              <div>
                <span className="text-small font-semibold text-brand-800">LLM (Claude)</span>
                <span className="text-small text-brand-500"> — para síntese de respostas acessíveis</span>
              </div>
            </div>
          </div>
        </section>

        {/* Fontes */}
        <section>
          <h2 className="text-caption font-medium uppercase tracking-wider text-brand-400 mb-3">
            Fontes de dados
          </h2>
          <div className="space-y-2">
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

        {/* Contexto acadêmico */}
        <section>
          <h2 className="text-caption font-medium uppercase tracking-wider text-brand-400 mb-3">
            Contexto acadêmico
          </h2>
          <p className="text-body text-brand-700 leading-relaxed max-w-[560px]">
            Trabalho de Conclusão de Curso em Sistemas de Informação com o tema
            "Arquitetura RAG Híbrida para Consulta em Linguagem Natural a Dados
            de Emendas Parlamentares Brasileiras".
          </p>
        </section>

        {/* Disclaimer */}
        <section className="border-t border-surface-200 pt-8">
          <div className="flex items-start gap-2.5 text-small text-brand-500">
            <AlertTriangle size={14} className="text-caution-500 mt-0.5 shrink-0" />
            <p className="leading-relaxed max-w-[560px]">
              As respostas são geradas por inteligência artificial e podem conter
              imprecisões. Sempre verifique as informações nas fontes oficiais indicadas.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
