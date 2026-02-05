"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Grape, Send, Database, FileText, Network, ChevronDown, Loader2, MessageSquare, Leaf, Bug, Pill, Camera, Upload, X, ImageIcon, AlertTriangle, CheckCircle } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  graphContext?: string
  pdfContext?: string
}

interface ImageAnalysisResult {
  disease: string
  confidence: number
  severity: "low" | "medium" | "high"
  treatment: string
  description: string
}

export default function GrapeGraphRAG() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [language, setLanguage] = useState("English")
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<ImageAnalysisResult | null>(null)

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setSelectedImage(reader.result as string)
        setAnalysisResult(null)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleImageDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setSelectedImage(reader.result as string)
        setAnalysisResult(null)
      }
      reader.readAsDataURL(file)
    }
  }

  const analyzeImage = async () => {
    if (!selectedImage) return
    setIsAnalyzing(true)

    // Simulated analysis for demo
    setTimeout(() => {
      const diseases = [
        {
          disease: "Powdery Mildew",
          confidence: 92,
          severity: "medium" as const,
          treatment: "Apply sulfur-based fungicide (e.g., Microthiol) at 2-3 kg/ha. Repeat every 10-14 days.",
          description: "White powdery spots detected on leaf surface. Common fungal disease affecting grape foliage and fruit."
        },
        {
          disease: "Downy Mildew",
          confidence: 87,
          severity: "high" as const,
          treatment: "Use copper-based fungicide (Bordeaux mixture) preventively. Apply mancozeb for active infections.",
          description: "Yellow oily spots on upper leaf surface with white downy growth underneath. Requires immediate attention."
        },
        {
          disease: "Black Rot",
          confidence: 78,
          severity: "low" as const,
          treatment: "Remove infected plant material. Apply captan or myclobutanil fungicide during early growth stages.",
          description: "Brown lesions with dark borders detected. Early-stage infection that can be managed effectively."
        }
      ]
      setAnalysisResult(diseases[Math.floor(Math.random() * diseases.length)])
      setIsAnalyzing(false)
    }, 2500)
  }

  const clearImage = () => {
    setSelectedImage(null)
    setAnalysisResult(null)
  }

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
          <Tabs defaultValue="chat" className="flex flex-1 flex-col">
            <Card className="flex flex-1 flex-col">
              <CardHeader className="border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Grape className="h-5 w-5 text-emerald-600" />
                      Grape-Mind AI Assistant
                    </CardTitle>
                    <CardDescription>
                      Powered by hybrid Graph + Vector retrieval for accurate agricultural insights
                    </CardDescription>
                  </div>
                  <TabsList className="grid w-[240px] grid-cols-2">
                    <TabsTrigger value="chat" className="gap-1.5">
                      <MessageSquare className="h-4 w-4" />
                      Chat
                    </TabsTrigger>
                    <TabsTrigger value="image" className="gap-1.5">
                      <Camera className="h-4 w-4" />
                      Image
                    </TabsTrigger>
                  </TabsList>
                </div>
              </CardHeader>

              <TabsContent value="chat" className="m-0 flex flex-1 flex-col">

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
              </TabsContent>

              <TabsContent value="image" className="m-0 flex flex-1 flex-col p-4">
                <div className="flex flex-1 flex-col gap-4 lg:flex-row">
                  {/* Upload Area */}
                  <div className="flex flex-1 flex-col">
                    {!selectedImage ? (
                      <div
                        onDrop={handleImageDrop}
                        onDragOver={(e) => e.preventDefault()}
                        className="flex flex-1 flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 bg-muted/30 p-8 transition-colors hover:border-emerald-500/50 hover:bg-muted/50"
                      >
                        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                          <ImageIcon className="h-8 w-8 text-emerald-600" />
                        </div>
                        <h3 className="mb-2 text-lg font-medium">Upload Grape Leaf Image</h3>
                        <p className="mb-4 max-w-sm text-center text-sm text-muted-foreground">
                          Drag and drop an image of a grape leaf, or click to browse. Our AI will analyze it for diseases.
                        </p>
                        <label htmlFor="image-upload">
                          <Button asChild className="cursor-pointer bg-emerald-600 hover:bg-emerald-700">
                            <span>
                              <Upload className="mr-2 h-4 w-4" />
                              Choose Image
                            </span>
                          </Button>
                          <input
                            id="image-upload"
                            type="file"
                            accept="image/*"
                            onChange={handleImageUpload}
                            className="hidden"
                          />
                        </label>
                      </div>
                    ) : (
                      <div className="flex flex-1 flex-col">
                        <div className="relative flex-1 overflow-hidden rounded-lg border bg-muted/30">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={clearImage}
                            className="absolute right-2 top-2 z-10 h-8 w-8 bg-background/80 backdrop-blur-sm hover:bg-background"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                          <img
                            src={selectedImage}
                            alt="Uploaded grape leaf"
                            className="h-full w-full object-contain"
                          />
                        </div>
                        <div className="mt-4 flex gap-2">
                          <label htmlFor="image-reupload" className="flex-1">
                            <Button variant="outline" asChild className="w-full cursor-pointer">
                              <span>
                                <Upload className="mr-2 h-4 w-4" />
                                Change Image
                              </span>
                            </Button>
                            <input
                              id="image-reupload"
                              type="file"
                              accept="image/*"
                              onChange={handleImageUpload}
                              className="hidden"
                            />
                          </label>
                          <Button
                            onClick={analyzeImage}
                            disabled={isAnalyzing}
                            className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                          >
                            {isAnalyzing ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <Camera className="mr-2 h-4 w-4" />
                                Analyze Image
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Analysis Results */}
                  <div className="w-full lg:w-80">
                    <Card className="h-full">
                      <CardHeader className="pb-3">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Bug className="h-4 w-4 text-emerald-600" />
                          Analysis Results
                        </CardTitle>
                        <CardDescription>Disease detection and treatment recommendations</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {!selectedImage && !analysisResult && (
                          <div className="flex flex-col items-center py-8 text-center text-muted-foreground">
                            <ImageIcon className="mb-2 h-8 w-8 opacity-50" />
                            <p className="text-sm">Upload an image to get started</p>
                          </div>
                        )}

                        {selectedImage && !analysisResult && !isAnalyzing && (
                          <div className="flex flex-col items-center py-8 text-center text-muted-foreground">
                            <Camera className="mb-2 h-8 w-8 opacity-50" />
                            <p className="text-sm">Click &quot;Analyze Image&quot; to detect diseases</p>
                          </div>
                        )}

                        {isAnalyzing && (
                          <div className="flex flex-col items-center py-8 text-center">
                            <Loader2 className="mb-3 h-8 w-8 animate-spin text-emerald-600" />
                            <p className="text-sm font-medium">Analyzing leaf image...</p>
                            <p className="text-xs text-muted-foreground">Detecting patterns and diseases</p>
                          </div>
                        )}

                        {analysisResult && (
                          <div className="space-y-4">
                            <div className="rounded-lg bg-muted/50 p-3">
                              <div className="mb-2 flex items-center justify-between">
                                <span className="text-sm font-medium">{analysisResult.disease}</span>
                                <Badge 
                                  variant={analysisResult.severity === "high" ? "destructive" : analysisResult.severity === "medium" ? "default" : "secondary"}
                                  className={analysisResult.severity === "medium" ? "bg-amber-500" : ""}
                                >
                                  {analysisResult.severity} severity
                                </Badge>
                              </div>
                              <div className="mb-2 flex items-center gap-2">
                                <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                                  <div 
                                    className="h-full bg-emerald-600 transition-all"
                                    style={{ width: `${analysisResult.confidence}%` }}
                                  />
                                </div>
                                <span className="text-xs text-muted-foreground">{analysisResult.confidence}%</span>
                              </div>
                              <p className="text-xs text-muted-foreground">{analysisResult.description}</p>
                            </div>

                            <div className="space-y-2">
                              <div className="flex items-center gap-2 text-sm font-medium">
                                <CheckCircle className="h-4 w-4 text-emerald-600" />
                                Recommended Treatment
                              </div>
                              <p className="rounded-lg bg-emerald-50 p-3 text-xs text-emerald-800">
                                {analysisResult.treatment}
                              </p>
                            </div>

                            <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3">
                              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                              <p className="text-xs text-amber-800">
                                This is an AI-powered analysis. For best results, consult with a local agricultural expert before applying treatments.
                              </p>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </TabsContent>
            </Card>
          </Tabs>
        </main>
      </div>
    </div>
  )
}
