import { ExternalLink } from 'lucide-react'

interface SourceLinkProps {
  url: string
  label: string
}

export function SourceLink({ url, label }: SourceLinkProps) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-caption px-2.5 py-1
                 border border-surface-200 rounded-md
                 text-brand-500 hover:text-brand-700 hover:border-brand-300 transition-colors"
    >
      <ExternalLink size={12} />
      {label}
    </a>
  )
}
