import { Routes, Route, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Database } from 'lucide-react'
import clsx from 'clsx'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import AboutPage from './pages/AboutPage'
import { checkHealth } from './services/api'

export default function App() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    retry: 2,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  })

  const dbDown = health.isError || (health.data && health.data.database !== 'connected')

  return (
    <div className="min-h-screen flex flex-col">
      {/* Database status banner */}
      {dbDown && (
        <div className="status-banner bg-destructive-50 text-destructive-600 border-b border-destructive-500/20 flex items-center justify-center gap-2">
          <Database size={14} />
          <span>
            O banco de dados está indisponível no momento. As consultas podem não funcionar corretamente.
          </span>
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-surface-200">
        <div className="max-w-wide mx-auto h-14 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="w-1.5 h-6 bg-accent-400 rounded-sm" />
            <span className="text-lg font-bold tracking-tight text-brand-900">
              Fiscalia
            </span>
          </NavLink>

          <nav className="flex items-center gap-4 sm:gap-6 text-small">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                clsx(
                  'transition-colors hover:text-brand-600',
                  isActive ? 'text-brand-900 font-medium' : 'text-brand-500'
                )
              }
            >
              Consultar
            </NavLink>
            <NavLink
              to="/results"
              className={({ isActive }) =>
                clsx(
                  'transition-colors hover:text-brand-600',
                  isActive ? 'text-brand-900 font-medium' : 'text-brand-500'
                )
              }
            >
              Explorar
            </NavLink>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                clsx(
                  'transition-colors hover:text-brand-600',
                  isActive ? 'text-brand-900 font-medium' : 'text-brand-500'
                )
              }
            >
              Sobre
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-200 bg-brand-950 text-brand-400">
        <div className="max-w-wide mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-1.5 h-5 bg-accent-400 rounded-sm" />
                <span className="font-bold text-white">Fiscalia</span>
              </div>
              <p className="text-caption text-brand-400 leading-relaxed">
                Iniciativa acadêmica sem fins lucrativos.
              </p>
            </div>

            <div>
              <p className="text-caption font-medium text-brand-300 mb-3 uppercase tracking-wider">
                Fontes de dados
              </p>
              <div className="space-y-1.5">
                <a
                  href="https://portaldatransparencia.gov.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-400 hover:text-white transition-colors"
                >
                  Portal da Transparência
                </a>
                <a
                  href="https://dadosabertos.camara.leg.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-400 hover:text-white transition-colors"
                >
                  Câmara dos Deputados
                </a>
              </div>
            </div>

            <div>
              <p className="text-caption font-medium text-brand-300 mb-3 uppercase tracking-wider">
                Projeto
              </p>
              <div className="space-y-1.5">
                <NavLink
                  to="/about"
                  className="block text-small text-brand-400 hover:text-white transition-colors"
                >
                  Sobre
                </NavLink>
                <a
                  href="https://github.com/anonymus-astro/Fiscalia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-400 hover:text-white transition-colors"
                >
                  Código fonte
                </a>
              </div>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-brand-800 flex flex-col sm:flex-row justify-between gap-2 text-caption text-brand-500">
            <div className="flex items-center gap-1.5">
              <AlertTriangle size={11} />
              <span>Respostas geradas por IA — verifique sempre nas fontes oficiais.</span>
            </div>
            <p>2024–2026</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
