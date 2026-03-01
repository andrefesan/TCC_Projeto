export interface QueryMetadata {
  latencia_ms: number
  entidades: Record<string, unknown>
  modo: string
  num_resultados: number
}

export interface QueryResponse {
  resposta: string
  fontes: string[]
  dados: EmendaData[]
  metadata: QueryMetadata
}

export interface EmendaData {
  id: number
  codigo_emenda?: string
  nome_autor?: string
  ano: number
  tipo_emenda?: string
  funcao_nome?: string
  subfuncao_nome?: string
  uf?: string
  localidade?: string
  valor_empenhado: number
  valor_liquidado: number
  valor_pago: number
  partido?: string
}

export interface ParlamentarData {
  cod_autor: number
  nome: string
  partido?: string
  uf?: string
  url_foto?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface HealthResponse {
  status: string
  database: string
  timestamp: string
  version: string
}
