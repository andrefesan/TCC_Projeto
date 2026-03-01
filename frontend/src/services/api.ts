import axios from 'axios'
import type { QueryResponse, EmendaData, PaginatedResponse } from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

export async function enviarConsulta(consulta: string): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', { consulta })
  return data
}

export async function buscarEmendas(
  params: Record<string, string | number>
): Promise<PaginatedResponse<EmendaData>> {
  const { data } = await api.get('/emendas', { params })
  return data
}

export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}
