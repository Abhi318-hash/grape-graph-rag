"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Grape, Send, Database, FileText, Network, ChevronDown, Loader2, MessageSquare, Leaf, Bug, Pill } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  graphContext?: string
  pdfContext?: string
}

export default function GrapeGraphRAG() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [language, setLanguage] = useState("English")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulated response for demo
    setTimeout(() => {
      const assistantMessage: Message = {
        role: "assistant",
        content: `Based on the knowledge graph and PDF manuals, here's information about "${input}":\n\nThis is a demo interface for the Grape-Mind AI system. In the full implementation, this would connect to Neo4j for graph data and ChromaDB for vector search to provide comprehensive answers about grape varieties, diseases, and treatments.`,
        graphContext: "Demo: Graph database connection required",
        pdfContext: "Demo: ChromaDB vector store connection required",
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-600 text-white">
              <Grape className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Grape-Mind AI</h1>
              <p className="text-sm text-muted-foreground">Agri-Tech Graph RAG</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="English">English</SelectItem>
                <SelectItem value="Hindi">Hindi</SelectItem>
                <SelectItem value="Marathi">Marathi</SelectItem>
                <SelectItem value="Kannada">Kannada</SelectItem>
                <SelectItem value="Telugu">Telugu</SelectItem>
              </SelectContent>
            </Select>
            <Badge variant="outline" className="gap-1.5 border-emerald-500/50 bg-emerald-500/10 text-emerald-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              System Online
            </Badge>
          </div>
        </div>
      </header>

      <div className="container mx-auto flex gap-6 p-6">
        {/* Sidebar */}
        <aside className="hidden w-72 shrink-0 space-y-4 lg:block">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Network className="h-4 w-4 text-emerald-600" />
                Knowledge Graph
              </CardTitle>
              <CardDescription>Connected entities and relationships</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
                <Leaf className="h-4 w-4 text-green-600" />
                <span className="text-sm">Grape Varieties</span>
                <Badge variant="secondary" className="ml-auto text-xs">12</Badge>
              </div>
              <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
                <Bug className="h-4 w-4 text-red-600" />
                <span className="text-sm">Diseases</span>
                <Badge variant="secondary" className="ml-auto text-xs">8</Badge>
              </div>
              <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
                <Pill className="h-4 w-4 text-blue-600" />
                <span className="text-sm">Treatments</span>
                <Badge variant="secondary" className="ml-auto text-xs">15</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Database className="h-4 w-4 text-emerald-600" />
                Data Sources
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Neo4j Graph</span>
                <Badge variant="outline" className="text-xs">Connected</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">ChromaDB</span>
                <Badge variant="outline" className="text-xs">Connected</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">PDF Documents</span>
                <Badge variant="outline" className="text-xs">2 files</Badge>
              </div>
            </CardContent>
          </Card>
        </aside>

        {/* Main Chat Area */}
        <main className="flex flex-1 flex-col">
          <Card className="flex flex-1 flex-col">
            <CardHeader className="border-b">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-emerald-600" />
                Ask about Grapes, Diseases, or Treatments
              </CardTitle>
              <CardDescription>
                Powered by hybrid Graph + Vector retrieval for accurate agricultural insights
              </CardDescription>
            </CardHeader>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                      <Grape className="h-8 w-8 text-emerald-600" />
                    </div>
                    <h3 className="mb-2 text-lg font-medium">Welcome to Grape-Mind AI</h3>
                    <p className="mb-6 max-w-md text-sm text-muted-foreground">
                      Ask questions about grape varieties, diseases, treatments, and agricultural best practices.
                    </p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {["How do I treat Chardonnay?", "What causes powdery mildew?", "Best fungicides for grapes"].map(
                        (example) => (
                          <Button
                            key={example}
                            variant="outline"
                            size="sm"
                            onClick={() => setInput(example)}
                            className="text-xs"
                          >
                            {example}
                          </Button>
                        )
                      )}
                    </div>
                  </div>
                )}

                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        message.role === "user"
                          ? "bg-emerald-600 text-white"
                          : "bg-muted"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm">{message.content}</p>

                      {message.role === "assistant" && message.graphContext && (
                        <Collapsible className="mt-3">
                          <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
                              <ChevronDown className="h-3 w-3" />
                              See System Reasoning
                            </Button>
                          </CollapsibleTrigger>
                          <CollapsibleContent className="mt-2 space-y-2">
                            <div className="rounded bg-blue-50 p-2 text-xs text-blue-700">
                              <strong>Graph Facts:</strong> {message.graphContext}
                            </div>
                            <div className="rounded bg-amber-50 p-2 text-xs text-amber-700">
                              <strong>PDF Context:</strong> {message.pdfContext}
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-center gap-2 rounded-lg bg-muted p-4">
                      <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
                      <span className="text-sm text-muted-foreground">
                        Analyzing PDF Manuals & Graph Database...
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="border-t p-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ex: How do I treat Chardonnay?"
                  className="flex-1"
                  disabled={isLoading}
                />
                <Button type="submit" disabled={isLoading || !input.trim()} className="bg-emerald-600 hover:bg-emerald-700">
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </Card>
        </main>
      </div>
    </div>
  )
}
