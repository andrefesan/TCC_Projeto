export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Sobre o Projeto</h1>

      <div className="space-y-6 text-gray-600 leading-relaxed">
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">O que é</h2>
          <p>
            A <strong>Transparência Fiscal</strong> é uma plataforma que permite
            ao cidadão consultar dados sobre emendas parlamentares federais
            brasileiras em linguagem natural, recebendo respostas fundamentadas
            com citações verificáveis de fontes governamentais.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Como funciona</h2>
          <p>
            O sistema utiliza uma arquitetura de RAG (Retrieval-Augmented Generation)
            híbrido que combina:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li><strong>Text-to-SQL:</strong> para consultas estruturadas (autor, ano, UF)</li>
            <li><strong>Busca vetorial semântica:</strong> para termos que exigem interpretação</li>
            <li><strong>LLM (Claude):</strong> para síntese de respostas acessíveis</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Fontes de dados</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <a href="https://portaldatransparencia.gov.br" target="_blank"
                 rel="noopener noreferrer" className="text-primary-600 hover:underline">
                Portal da Transparência (CGU)
              </a> — dados de emendas parlamentares
            </li>
            <li>
              <a href="https://dadosabertos.camara.leg.br" target="_blank"
                 rel="noopener noreferrer" className="text-primary-600 hover:underline">
                Câmara dos Deputados — Dados Abertos
              </a> — dados de parlamentares
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Trabalho acadêmico</h2>
          <p>
            Esta plataforma foi desenvolvida como parte do TCC
            &quot;Arquitetura de Plataforma Baseada em LLM e RAG para Consulta
            Inteligente de Dados de Transparência Fiscal&quot; do curso de
            Sistemas de Informação da Universidade Federal do Acre (UFAC).
          </p>
          <p className="mt-2">
            <strong>Autor:</strong> André Ferreira Santana
          </p>
        </section>

        <section className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm">
          <strong>Aviso:</strong> As respostas são geradas por inteligência
          artificial e podem conter imprecisões. Sempre verifique as informações
          nas fontes oficiais indicadas.
        </section>
      </div>
    </div>
  )
}
