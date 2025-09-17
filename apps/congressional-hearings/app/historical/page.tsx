"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Archive, Calendar, FileText, Users, ExternalLink, Download, Search, Filter } from "lucide-react"
import Link from "next/link"

// Mock data for historical hearings
const historicalHearings = [
  {
    id: 1,
    title: "Social Media Platform Accountability",
    committee: "House Committee on Energy and Commerce",
    date: "2023-12-15",
    transcriptStatus: "available",
    witnesses: ["Mark Zuckerberg", "Elon Musk", "Linda Yaccarino"],
    pages: 247,
    citations: 34,
    relatedDocs: 18,
    topics: ["Social Media", "Privacy", "Content Moderation"],
    summary: "Hearing on social media platform accountability and content moderation practices.",
  },
  {
    id: 2,
    title: "Federal Reserve Monetary Policy Review",
    committee: "Senate Committee on Banking, Housing, and Urban Affairs",
    date: "2023-11-28",
    transcriptStatus: "processing",
    witnesses: ["Jerome Powell", "Janet Yellen"],
    pages: 189,
    citations: 28,
    relatedDocs: 12,
    topics: ["Monetary Policy", "Interest Rates", "Inflation"],
    summary: "Semi-annual monetary policy report and economic outlook discussion.",
  },
  {
    id: 3,
    title: "Climate Change and Energy Infrastructure",
    committee: "House Committee on Science, Space, and Technology",
    date: "2023-10-22",
    transcriptStatus: "available",
    witnesses: ["Dr. Michael Mann", "Jennifer Granholm", "Dr. Susan Solomon"],
    pages: 312,
    citations: 67,
    relatedDocs: 25,
    topics: ["Climate Change", "Energy", "Infrastructure"],
    summary: "Examination of climate change impacts on energy infrastructure and adaptation strategies.",
  },
  {
    id: 4,
    title: "Artificial Intelligence in Healthcare",
    committee: "Senate Committee on Health, Education, Labor and Pensions",
    date: "2023-09-18",
    transcriptStatus: "available",
    witnesses: ["Dr. Eric Topol", "Dr. Regina Barzilay", "Dr. Blackford Middleton"],
    pages: 156,
    citations: 42,
    relatedDocs: 15,
    topics: ["AI", "Healthcare", "Medical Technology"],
    summary: "Exploring the potential and challenges of AI implementation in healthcare systems.",
  },
  {
    id: 5,
    title: "Cybersecurity Threats to Critical Infrastructure",
    committee: "House Committee on Homeland Security",
    date: "2023-08-14",
    transcriptStatus: "available",
    witnesses: ["Christopher Wray", "Jen Easterly", "Rob Joyce"],
    pages: 203,
    citations: 31,
    relatedDocs: 22,
    topics: ["Cybersecurity", "Infrastructure", "National Security"],
    summary: "Assessment of cybersecurity threats facing critical infrastructure sectors.",
  },
  {
    id: 6,
    title: "Student Loan Debt Crisis",
    committee: "Senate Committee on Health, Education, Labor and Pensions",
    date: "2023-07-11",
    transcriptStatus: "available",
    witnesses: ["Miguel Cardona", "Dr. Beth Akers", "Persis Yu"],
    pages: 178,
    citations: 23,
    relatedDocs: 14,
    topics: ["Education", "Student Loans", "Higher Education"],
    summary: "Examining the student loan debt crisis and potential policy solutions.",
  },
]

const committees = [
  "All Committees",
  "House Committee on Energy and Commerce",
  "Senate Committee on Banking, Housing, and Urban Affairs",
  "House Committee on Science, Space, and Technology",
  "Senate Committee on Health, Education, Labor and Pensions",
  "House Committee on Homeland Security",
]

const topics = [
  "All Topics",
  "AI",
  "Climate Change",
  "Cybersecurity",
  "Education",
  "Energy",
  "Healthcare",
  "Infrastructure",
  "Monetary Policy",
  "National Security",
  "Privacy",
  "Social Media",
]

export default function HistoricalHearings() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCommittee, setSelectedCommittee] = useState("All Committees")
  const [selectedTopic, setSelectedTopic] = useState("All Topics")
  const [dateRange, setDateRange] = useState("all")

  const filteredHearings = historicalHearings.filter((hearing) => {
    const matchesSearch =
      hearing.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hearing.committee.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hearing.witnesses.some((witness) => witness.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesCommittee = selectedCommittee === "All Committees" || hearing.committee === selectedCommittee
    const matchesTopic = selectedTopic === "All Topics" || hearing.topics.some((topic) => topic === selectedTopic)

    let matchesDate = true
    if (dateRange !== "all") {
      const hearingDate = new Date(hearing.date)
      const now = new Date()
      const monthsAgo = Number.parseInt(dateRange)
      const cutoffDate = new Date(now.getFullYear(), now.getMonth() - monthsAgo, now.getDate())
      matchesDate = hearingDate >= cutoffDate
    }

    return matchesSearch && matchesCommittee && matchesTopic && matchesDate
  })

  const getTranscriptStatusColor = (status: string) => {
    switch (status) {
      case "available":
        return "bg-green-100 text-green-800 border-green-200"
      case "processing":
        return "bg-orange-100 text-orange-800 border-orange-200"
      case "unavailable":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-balance">Historical Hearings</h1>
          <p className="text-muted-foreground mt-2">Browse and analyze past committee hearings and transcripts</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/search">
              <Search className="mr-2 h-4 w-4" />
              Advanced Search
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Hearings</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">Since 2020</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transcripts Available</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,089</div>
            <p className="text-xs text-muted-foreground">87% coverage</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Citations Tracked</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12,456</div>
            <p className="text-xs text-muted-foreground">Cross-referenced</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Related Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8,923</div>
            <p className="text-xs text-muted-foreground">Linked resources</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Search & Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Search hearings, witnesses..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Committee</label>
              <Select value={selectedCommittee} onValueChange={setSelectedCommittee}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {committees.map((committee) => (
                    <SelectItem key={committee} value={committee}>
                      {committee}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Topic</label>
              <Select value={selectedTopic} onValueChange={setSelectedTopic}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {topics.map((topic) => (
                    <SelectItem key={topic} value={topic}>
                      {topic}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Date Range</label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="3">Last 3 months</SelectItem>
                  <SelectItem value="6">Last 6 months</SelectItem>
                  <SelectItem value="12">Last year</SelectItem>
                  <SelectItem value="24">Last 2 years</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm("")
                  setSelectedCommittee("All Committees")
                  setSelectedTopic("All Topics")
                  setDateRange("all")
                }}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Hearings List */}
      <div className="space-y-4">
        {filteredHearings.map((hearing) => (
          <Card key={hearing.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <CardTitle className="text-xl text-balance">{hearing.title}</CardTitle>
                  <CardDescription>{hearing.committee}</CardDescription>
                  <p className="text-sm text-muted-foreground">{hearing.summary}</p>
                </div>
                <Badge className={getTranscriptStatusColor(hearing.transcriptStatus)}>{hearing.transcriptStatus}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{new Date(hearing.date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.pages} pages</span>
                </div>
                <div className="flex items-center gap-2">
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.citations} citations</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.witnesses.length} witnesses</span>
                </div>
              </div>

              {/* Topics */}
              <div className="mb-4">
                <div className="flex flex-wrap gap-2">
                  {hearing.topics.map((topic, index) => (
                    <Badge key={index} variant="secondary">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Witnesses */}
              <div className="mb-4">
                <h4 className="text-sm font-medium mb-2">Witnesses:</h4>
                <div className="flex flex-wrap gap-2">
                  {hearing.witnesses.map((witness, index) => (
                    <Badge key={index} variant="outline">
                      {witness}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">{hearing.relatedDocs} related documents</div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Download className="mr-1 h-3 w-3" />
                      Download
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/historical/${hearing.id}/documents`}>View Documents</Link>
                    </Button>
                    <Button size="sm" asChild>
                      <Link href={`/historical/${hearing.id}/transcript`}>
                        {hearing.transcriptStatus === "available" ? "View Transcript" : "Check Status"}
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredHearings.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Archive className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No hearings found</h3>
            <p className="text-muted-foreground">Try adjusting your filters or search terms.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
