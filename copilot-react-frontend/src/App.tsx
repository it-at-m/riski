import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { CopilotKit, useCoAgentStateRender, useCopilotChat, useCopilotContext } from '@copilotkit/react-core'
import { TextMessage, MessageRole } from '@copilotkit/runtime-client-gql'
import '@copilotkit/react-ui/styles.css'

const RISKI_AGENT_NAME = 'riski_agent'
const SIDEBAR_INSTRUCTIONS = `Du bist der RISKI-RAG-Assistent. Analysiere Ratsinformationen, zitiere relevante Dokument- und Beschluss-IDs und weise transparent auf Unsicherheit oder fehlende Daten hin.`

type DocumentMetadata = {
  id?: string
  identifier?: string
  name?: string
  risUrl?: string
  source?: string
  score?: number
  size?: number
  [key: string]: unknown
}

type RiskiDocument = {
  page_content?: string
  metadata?: DocumentMetadata
}

type RiskiAgentState = {
  documents?: RiskiDocument[]
  proposals?: RiskiDocument[]
}

type NodeHistoryEntry = {
  id: string
  label: string
  timestamp: number
}


function App() {
  return (
    <CopilotKit runtimeUrl="http://localhost:4000/copilotkit" agent={RISKI_AGENT_NAME}>
      <MainLayout />
    </CopilotKit>
  )
}

function MainLayout() {
  useChatInstructionSync(SIDEBAR_INSTRUCTIONS)
  const insights = useRiskiAgentInsights()

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="w-full max-w-5xl mx-auto py-10 px-6 lg:px-8 flex flex-col gap-8 text-slate-900">
        <HeroSection />
        <LiveUpdatePanel nodeName={insights.nodeName} nodeHistory={insights.nodeHistory} />
        <ChatInput />
        <ContextPanel state={insights.state} />
      </div>
    </div>
  )
}

function HeroSection() {
  const infoTiles = [
    { label: 'LangGraph Agent', value: 'v1.0' },
    {
      label: 'Letzte Aktualisierung',
      value: new Intl.DateTimeFormat('de-DE', { month: 'long', year: 'numeric' }).format(new Date()),
    },
    { label: 'Abgedeckte Quellen', value: 'RIS München' },
  ]

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-10 shadow-xl shadow-slate-200/60">
      <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">Research Preview</p>
      <h1 className="mt-4 text-4xl md:text-5xl font-semibold text-slate-900 leading-tight">
        RIS KI Suche (Beta-Version)
      </h1>
      <p className="mt-4 text-lg text-slate-600 max-w-3xl">
        Hier können Sie Ihre Frage zu öffentlich verfügbaren Inhalten aus dem Ratsinformationssystem (RIS) stellen. Die Suche liefert ihnen dann eine zusammenfassende Antwort sowie relevante Dokumente und die Bezeichnungen relevanter Anträge.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {infoTiles.map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

type LiveUpdatePanelProps = {
  nodeName: string | null
  nodeHistory: NodeHistoryEntry[]
}

function LiveUpdatePanel({ nodeName, nodeHistory }: LiveUpdatePanelProps) {
  const hasProgress = nodeHistory.length > 0

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-1">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Live Update</p>
        <h2 className="text-2xl font-semibold text-slate-900">LangGraph Fortschritt</h2>
        <p className="text-sm text-slate-500">
          {nodeName ? `Aktiver Knoten: ${nodeName}` : 'Noch keine Ausführung – stelle eine Frage, um den Agenten zu starten.'}
        </p>
      </div>

      <div className="mt-6">
        {hasProgress ? (
          <ol className="space-y-4">
            {nodeHistory.map((entry, index) => (
              <li key={entry.id} className="flex items-start gap-4">
                <div className="flex flex-col items-center text-sky-600">
                  <span className="text-xs font-semibold">{index + 1}</span>
                  {index < nodeHistory.length - 1 && <span className="mt-1 h-8 w-px bg-sky-500/40" />}
                </div>
                <div className="flex-1 rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <p className="text-sm font-semibold text-slate-900">{entry.label}</p>
                  <p className="text-xs text-slate-500">
                    {new Date(entry.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-slate-500">
            Jede Agenten-Aktion erscheint hier als Schritt – so behältst du während der Recherche den Überblick.
          </p>
        )}
      </div>
    </section>
  )
}

type ContextPanelProps = {
  state: RiskiAgentState | null
}

function ContextPanel({ state }: ContextPanelProps) {
  const documents = state?.documents ?? []
  const proposals = state?.proposals ?? []
  const hasInsights = documents.length > 0 || proposals.length > 0

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-1">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Kontext</p>
        <h2 className="text-2xl font-semibold text-slate-900">Retriever Snapshot</h2>
        <p className="text-sm text-slate-500">
          Eingeblendete Dokumente und Beschlussvorlagen stammen aus dem aktuellen Lauf des RISKI-Agenten.
        </p>
      </div>

      <div className="mt-6 space-y-6">
        <DocumentSection title="Dokumente" documents={documents} emptyLabel="Noch keine Dokumente ausgewählt." />
        <DocumentSection title="Beschlussvorlagen" documents={proposals} emptyLabel="Keine Beschlussvorlagen im aktuellen Lauf." />
      </div>

      {!hasInsights && (
        <p className="mt-6 text-sm text-slate-500">
          Tipp: Frag zum Beispiel nach „Welche Risiken adressiert der aktuelle Stadtratsantrag zur sicheren KI?“ – der Agent streamt dann hier passende Quellen.
        </p>
      )}
    </section>
  )
}

type DocumentSectionProps = {
  title: string
  documents: RiskiDocument[]
  emptyLabel: string
}

function DocumentSection({ title, documents, emptyLabel }: DocumentSectionProps) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-0.5 text-xs text-slate-600">{documents.length}</span>
      </div>
      {documents.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">{emptyLabel}</p>
      ) : (
        <div className="mt-3 flex flex-col gap-3">
          {documents.map((doc, index) => (
            <DocumentCard key={doc.metadata?.id ?? doc.metadata?.identifier ?? index} document={doc} />
          ))}
        </div>
      )}
    </div>
  )
}

type DocumentCardProps = {
  document: RiskiDocument
}

function DocumentCard({ document }: DocumentCardProps) {
  const metadata = document.metadata ?? {}
  const title = metadata.name ?? metadata.identifier ?? 'Unbekanntes Dokument'
  const subtitle = metadata.identifier ?? metadata.source ?? 'Quelle unbekannt'
  const risUrl = metadata.risUrl
  const score = typeof metadata.score === 'number' ? `${Math.round(metadata.score * 100)}% Relevanz` : undefined

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm font-semibold text-slate-900">{title}</p>
        <span className="text-xs text-slate-500">{subtitle}</span>
        {score && <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700">{score}</span>}
      </div>
      {document.page_content && (
        <p className="mt-3 text-sm text-slate-600 line-clamp-3">{document.page_content}</p>
      )}
      <div className="mt-4 text-xs text-slate-500 flex flex-wrap gap-3">
        {metadata.risUrl && (
          <a
            href={risUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-600 hover:text-sky-700"
          >
            Quelle öffnen
          </a>
        )}
        {metadata.size && <span>{metadata.size} Seiten</span>}
      </div>
    </div>
  )
}

function ChatInput() {
  const { appendMessage, isLoading, stopGeneration } = useCopilotChat()
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = message.trim()
    if (!trimmed) {
      setError('Bitte gib eine Frage ein.')
      return
    }

    try {
      setError(null)
      await appendMessage(
        new TextMessage({
          role: MessageRole.User,
          content: trimmed,
        })
      )
      setMessage('')
    } catch (sendError) {
      console.error('Chat send error', sendError)
      setError('Senden fehlgeschlagen. Bitte erneut versuchen.')
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label htmlFor="riski-chat-input" className="text-sm uppercase tracking-[0.3em] text-slate-500">
          Frage an den RISKI Copilot
        </label>
        <textarea
          id="riski-chat-input"
          className="min-h-[140px] rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-200 focus:outline-none"
          placeholder="Formuliere deine Frage an den Stadtrats-Copilot ..."
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
        {error && <p className="text-sm text-amber-600">{error}</p>}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-sky-300"
          >
            {isLoading ? 'Antwort wird erstellt …' : 'Frage senden'}
          </button>
          {isLoading && (
            <button
              type="button"
              onClick={stopGeneration}
              className="text-sm text-slate-500 underline-offset-4 hover:underline"
            >
              Antwort stoppen
            </button>
          )}
          <p className="text-xs text-slate-500">Der Agent nutzt die RISKI-Anbindung zum LangGraph-Agenten.</p>
        </div>
      </form>
    </section>
  )
}

type UseRiskiAgentInsightsReturn = {
  state: RiskiAgentState | null
  nodeName: string | null
  nodeHistory: NodeHistoryEntry[]
}

function useRiskiAgentInsights(): UseRiskiAgentInsightsReturn {
  const [state, setState] = useState<RiskiAgentState | null>(null)
  const [nodeName, setNodeName] = useState<string | null>(null)
  const [nodeHistory, setNodeHistory] = useState<NodeHistoryEntry[]>([])

  const handleStateUpdate = useCallback(({ state, nodeName }: { state: RiskiAgentState; nodeName: string }) => {
    setState(state)
    setNodeName(nodeName)
    if (!nodeName) {
      return
    }
    setNodeHistory((previous) => {
      const lastEntry = previous[previous.length - 1]
      if (lastEntry?.label === nodeName) {
        return previous
      }
      return [
        ...previous,
        {
          id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
          label: nodeName,
          timestamp: Date.now(),
        },
      ]
    })
  }, [])

  useCoAgentStateRender<RiskiAgentState>({
    name: RISKI_AGENT_NAME,
    handler: handleStateUpdate,
  }, [handleStateUpdate])

  return { state, nodeName, nodeHistory }
}

function useChatInstructionSync(instructions: string) {
  const { chatInstructions, setChatInstructions } = useCopilotContext()

  useEffect(() => {
    if (!instructions) {
      return
    }

    if (chatInstructions === instructions) {
      return
    }

    setChatInstructions(instructions)
  }, [instructions, chatInstructions, setChatInstructions])
}

export default App
