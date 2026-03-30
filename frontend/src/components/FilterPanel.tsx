import clsx from 'clsx'

interface FilterPanelProps {
  filters: Record<string, string>
  onChange: (filters: Record<string, string>) => void
}

const ANOS = ['2020', '2021', '2022', '2023', '2024']
const UFS = [
  'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS',
  'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC',
  'SE', 'SP', 'TO',
]
const PARTIDOS = ['PT', 'PL', 'MDB', 'PP', 'PSD', 'PSDB', 'UNIÃO', 'PDT', 'PSB', 'REPUBLICANOS']

const FILTER_CONFIG = [
  { key: 'ano', label: 'Ano', options: ANOS },
  { key: 'uf', label: 'Estado', options: UFS },
  { key: 'partido', label: 'Partido', options: PARTIDOS },
]

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const update = (key: string, value: string) => {
    const next = { ...filters }
    if (value) next[key] = value
    else delete next[key]
    onChange(next)
  }

  const activeCount = Object.keys(filters).length

  return (
    <div className="flex flex-wrap items-center gap-3">
      {FILTER_CONFIG.map(({ key, label, options }) => (
        <select
          key={key}
          value={filters[key] || ''}
          onChange={(e) => update(key, e.target.value)}
          className={clsx(
            'px-3 py-2 border rounded-md text-small bg-white transition-colors appearance-none pr-8',
            filters[key]
              ? 'border-brand-400 text-brand-800'
              : 'border-surface-200 text-brand-400'
          )}
        >
          <option value="">{label}</option>
          {options.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      ))}

      {activeCount > 0 && (
        <button
          onClick={() => onChange({})}
          className="text-caption text-brand-400 hover:text-destructive-500 transition-colors"
        >
          Limpar ({activeCount})
        </button>
      )}
    </div>
  )
}
