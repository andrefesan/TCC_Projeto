import { Loader2 } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="py-12">
      <div className="flex items-center gap-3 mb-4">
        <Loader2 size={18} className="text-brand-500 animate-spin" />
        <span className="text-body font-medium text-brand-800">Processando consulta</span>
      </div>
      <div className="space-y-2.5 max-w-md">
        <div className="h-3 bg-surface-200 rounded animate-pulse w-full" />
        <div className="h-3 bg-surface-200 rounded animate-pulse w-4/5" />
        <div className="h-3 bg-surface-200 rounded animate-pulse w-3/5" />
      </div>
      <p className="text-caption text-brand-400 mt-4">
        Buscando nos dados oficiais e gerando resposta fundamentada...
      </p>
    </div>
  )
}
