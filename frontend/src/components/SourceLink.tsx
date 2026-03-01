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
      className="inline-flex items-center gap-1 text-sm px-3 py-1
                 bg-success-50 text-success-500 rounded-full
                 hover:bg-green-100 transition"
    >
      <ExternalLink size={14} />
      {label}
    </a>
  )
}
