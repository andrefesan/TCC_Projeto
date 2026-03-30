import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import clsx from 'clsx'

interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading: boolean
  variant?: 'hero' | 'compact'
}

const SUGESTOES = [
  { text: 'Quais deputados mais destinaram emendas para saúde em 2024?', tema: 'Saúde' },
  { text: 'Emendas do senador Flávio Bolsonaro para o Rio de Janeiro', tema: 'Parlamentar' },
  { text: 'Quanto o PT destinou para educação entre 2020 e 2024?', tema: 'Partido' },
  { text: 'Maiores emendas para infraestrutura no Nordeste em 2023', tema: 'Região' },
  { text: 'Emendas de bancada para o estado de Minas Gerais', tema: 'Estado' },
  { text: 'Quais foram as emendas para segurança pública em São Paulo?', tema: 'Tema' },
  { text: 'Top 10 parlamentares por valor pago em 2024', tema: 'Ranking' },
  { text: 'Emendas destinadas à cultura no Rio Grande do Sul', tema: 'Estado' },
]

export function SearchBar({ onSearch, isLoading, variant = 'hero' }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query)
  }

  const isHero = variant === 'hero'

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Faça uma pergunta sobre emendas parlamentares..."
          className={clsx(
            'w-full bg-white border border-surface-200 outline-none transition-colors',
            'placeholder:text-brand-300',
            'focus:border-brand-400 focus:ring-1 focus:ring-brand-400',
            isHero
              ? 'text-body px-4 py-3.5 pr-28 rounded-lg'
              : 'text-small px-4 py-2.5 pr-24 rounded-md'
          )}
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className={clsx(
            'absolute flex items-center gap-1.5 font-medium transition-colors',
            'bg-brand-900 text-white rounded-md',
            'hover:bg-brand-800 disabled:opacity-40 disabled:cursor-not-allowed',
            isHero
              ? 'right-1.5 top-1.5 px-4 py-2 text-small'
              : 'right-1 top-1 px-3 py-1.5 text-caption'
          )}
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Search size={16} />
          )}
          Consultar
        </button>
      </form>

      {isHero && (
        <div className="mt-4">
          <p className="text-caption text-brand-400 mb-2">Experimente:</p>
          <div className="flex flex-wrap gap-2">
            {SUGESTOES.slice(0, 6).map((s, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(s.text)
                  onSearch(s.text)
                }}
                className="text-caption px-3 py-1.5 bg-white/70 border border-surface-200
                           rounded-md hover:border-brand-300 hover:text-brand-700 hover:bg-white
                           text-brand-500 transition-colors text-left"
              >
                {s.text}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
