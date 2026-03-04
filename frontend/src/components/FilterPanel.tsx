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

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const update = (key: string, value: string) => {
    const next = { ...filters }
    if (value) {
      next[key] = value
    } else {
      delete next[key]
    }
    onChange(next)
  }

  return (
    <div className="grid grid-cols-3 sm:flex sm:flex-wrap gap-3 items-center">
      <select
        value={filters.ano || ''}
        onChange={(e) => update('ano', e.target.value)}
        className="w-full sm:w-auto px-3 py-2 border rounded-lg text-sm bg-white"
      >
        <option value="">Ano</option>
        {ANOS.map((a) => <option key={a} value={a}>{a}</option>)}
      </select>

      <select
        value={filters.uf || ''}
        onChange={(e) => update('uf', e.target.value)}
        className="w-full sm:w-auto px-3 py-2 border rounded-lg text-sm bg-white"
      >
        <option value="">UF</option>
        {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
      </select>

      <select
        value={filters.partido || ''}
        onChange={(e) => update('partido', e.target.value)}
        className="w-full sm:w-auto px-3 py-2 border rounded-lg text-sm bg-white"
      >
        <option value="">Partido</option>
        {PARTIDOS.map((p) => <option key={p} value={p}>{p}</option>)}
      </select>

      {Object.keys(filters).length > 0 && (
        <button
          onClick={() => onChange({})}
          className="col-span-3 sm:col-span-1 text-xs text-gray-500 hover:text-danger-500 underline"
        >
          Limpar filtros
        </button>
      )}
    </div>
  )
}
