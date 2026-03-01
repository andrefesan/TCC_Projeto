import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading: boolean
}

const SUGESTOES = [
  'Emendas para saúde no Acre em 2024?',
  'Top 5 deputados que mais destinaram para educação?',
  'Quanto foi pago em emendas de bancada para o Amazonas?',
  'Houve aumento nas emendas para saneamento no Norte?',
  'Quais parlamentares do PT investiram em cultura?',
  'Emendas para segurança pública no Rio de Janeiro?',
]

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query)
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Digite sua pergunta sobre emendas parlamentares..."
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg
                     focus:ring-2 focus:ring-primary-500 focus:border-transparent
                     outline-none transition"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg
                     hover:bg-primary-700 disabled:opacity-50
                     flex items-center gap-2 transition font-medium"
        >
          {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Search size={20} />}
          Consultar
        </button>
      </form>

      <div className="flex flex-wrap gap-2 mt-4">
        {SUGESTOES.map((s, i) => (
          <button
            key={i}
            onClick={() => { setQuery(s); onSearch(s) }}
            className="text-xs px-3 py-1.5 bg-gray-100 rounded-full
                       hover:bg-primary-50 hover:text-primary-600
                       text-gray-600 transition"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
