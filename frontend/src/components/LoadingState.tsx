import { Loader2 } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="text-center py-16">
      <Loader2 size={48} className="mx-auto text-primary-500 animate-spin mb-4" />
      <p className="text-gray-500">Consultando dados e gerando resposta...</p>
      <p className="text-xs text-gray-400 mt-1">Isso pode levar alguns segundos</p>
    </div>
  )
}
