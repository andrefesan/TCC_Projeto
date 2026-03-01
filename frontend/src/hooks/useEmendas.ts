import { useQuery } from '@tanstack/react-query'
import { buscarEmendas } from '../services/api'

export function useEmendas(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['emendas', params],
    queryFn: () => buscarEmendas(params),
    enabled: Object.keys(params).length > 0,
  })
}
