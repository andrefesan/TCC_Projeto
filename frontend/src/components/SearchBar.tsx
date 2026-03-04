import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading: boolean
}

const SUGESTOES = [
  'Quais as emendas do deputado Roberto Duarte em 2024?',
  'Emendas para saúde no Acre em 2024?',
  'Quanto a Bancada do Acre destinou para defesa nacional?',
  'Top 5 parlamentares do Acre por valor empenhado?',
  'Emendas de Sergio Petecão para o Acre?',
  'Quais emendas foram destinadas a educação no Acre?',
]

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query)
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Digite sua pergunta sobre emendas parlamentares..."
          className="flex-1 min-w-0 px-4 py-3 border border-gray-300 rounded-lg
                     focus:ring-2 focus:ring-primary-500 focus:border-transparent
                     outline-none transition"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg
                     hover:bg-primary-700 disabled:opacity-50
                     flex items-center justify-center gap-2 transition font-medium
                     shrink-0"
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
