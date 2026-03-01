import { Search } from 'lucide-react'

export function EmptyState() {
  return (
    <div className="text-center py-16">
      <Search size={56} className="mx-auto text-gray-300 mb-4" />
      <h2 className="text-2xl font-bold text-gray-700 mb-2">
        Consulta Inteligente de Emendas Parlamentares
      </h2>
      <p className="text-gray-500 max-w-lg mx-auto">
        Faça perguntas em linguagem natural sobre emendas parlamentares federais.
        O sistema busca dados oficiais e gera respostas fundamentadas com citações
        verificáveis.
      </p>
    </div>
  )
}
