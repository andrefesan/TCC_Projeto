import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import AboutPage from './pages/AboutPage'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-primary-600 text-white py-4 px-4 sm:px-6 shadow-md">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <a href="/" className="text-xl font-bold tracking-tight">
            Transparência Fiscal
          </a>
          <nav className="flex gap-4 text-sm">
            <a href="/" className="hover:text-primary-100">Início</a>
            <a href="/about" className="hover:text-primary-100">Sobre</a>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>

      <footer className="bg-slate-800 text-slate-400 py-4 px-4 sm:px-6 text-center text-xs">
        <p className="flex flex-wrap justify-center gap-x-1">
          <span>Dados:</span>
          <a href="https://portaldatransparencia.gov.br" target="_blank" rel="noopener noreferrer" className="underline hover:text-white">Portal da Transparência</a>
          <span>|</span>
          <a href="https://dadosabertos.camara.leg.br" target="_blank" rel="noopener noreferrer" className="underline hover:text-white">Câmara dos Deputados</a>
        </p>
        <p className="mt-1 px-2">Respostas geradas por IA — verifique sempre nas fontes oficiais.</p>
        <p className="mt-0.5">TCC — André Ferreira Santana — UFAC</p>
      </footer>
    </div>
  )
}

export default App
