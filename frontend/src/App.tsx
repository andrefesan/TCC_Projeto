import { Routes, Route, NavLink } from 'react-router-dom'
import clsx from 'clsx'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import AboutPage from './pages/AboutPage'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-surface-200">
        <div className="max-w-wide mx-auto h-14 px-4 sm:px-6 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="w-1.5 h-6 bg-accent-400 rounded-sm" />
            <span className="text-lg font-bold tracking-tight text-brand-900">
              Fiscalia
            </span>
          </NavLink>

          <nav className="flex items-center gap-6 text-small">
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
      <footer className="border-t border-surface-200 bg-white">
        <div className="max-w-wide mx-auto px-4 sm:px-6 py-8">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
            <div className="max-w-xs">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-1.5 h-5 bg-accent-400 rounded-sm" />
                <span className="font-bold text-brand-900">Fiscalia</span>
              </div>
              <p className="text-caption text-brand-400 leading-relaxed">
                Projeto acadêmico sem fins lucrativos.
                Trabalho de Conclusão de Curso em Sistemas de Informação.
              </p>
            </div>

            <div>
              <p className="text-caption font-medium text-brand-600 mb-2 uppercase tracking-wider">
                Fontes de dados
              </p>
              <div className="space-y-1">
                <a
                  href="https://portaldatransparencia.gov.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-500 hover:text-brand-700 transition-colors"
                >
                  Portal da Transparência
                </a>
                <a
                  href="https://dadosabertos.camara.leg.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-500 hover:text-brand-700 transition-colors"
                >
                  Câmara dos Deputados
                </a>
              </div>
            </div>

            <div>
              <p className="text-caption font-medium text-brand-600 mb-2 uppercase tracking-wider">
                Projeto
              </p>
              <div className="space-y-1">
                <NavLink
                  to="/about"
                  className="block text-small text-brand-500 hover:text-brand-700 transition-colors"
                >
                  Sobre
                </NavLink>
                <a
                  href="https://github.com/anonymus-astro/Fiscalia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-small text-brand-500 hover:text-brand-700 transition-colors"
                >
                  Código fonte
                </a>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-surface-200 flex flex-col sm:flex-row justify-between gap-2 text-caption text-brand-400">
            <p>Respostas geradas por IA — verifique sempre nas fontes oficiais.</p>
            <p>2024–2026</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
