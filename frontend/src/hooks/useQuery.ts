import { useMutation } from '@tanstack/react-query'
import { enviarConsulta } from '../services/api'
import type { QueryResponse } from '../types'

export function useConsulta() {
  return useMutation<QueryResponse, Error, string>({
    mutationFn: enviarConsulta,
  })
}
