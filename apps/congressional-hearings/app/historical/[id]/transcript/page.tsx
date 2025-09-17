"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Calendar, Users, FileText, ExternalLink, ArrowLeft, Download, Quote, LinkIcon } from "lucide-react"
import Link from "next/link"

// Mock transcript data
const transcriptData = {
  id: 1,
  title: "Social Media Platform Accountability",
  committee: "House Committee on Energy and Commerce",
  date: "2023-12-15",
  witnesses: ["Mark Zuckerberg", "Elon Musk", "Linda Yaccarino"],
  pages: 247,
  citations: [
    {
      id: 1,
      text: "According to the 2023 Pew Research study on social media usage...",
      source: "Pew Research Center",
      page: 23,
      speaker: "Rep. Johnson",
      linkedDoc: "pew-social-media-2023.pdf",
    },
    {
      id: 2,
      text: "The GAO report from last year clearly states that platform oversight...",
      source: "GAO Report GAO-23-105",
      page: 45,
      speaker: "Rep. Smith",
      linkedDoc: "gao-23-105.pdf",
    },
    {
      id: 3,
      text: "As outlined in the CRS report on Section 230...",
      source: "CRS Report R46751",
      page: 78,
      speaker: "Mr. Zuckerberg",
      linkedDoc: "crs-r46751.pdf",
    },
  ],
  transcript: `
CHAIRMAN JOHNSON: The committee will come to order. Today we examine the accountability of social media platforms and their impact on American society.

Mr. Zuckerberg, thank you for appearing before the committee today. Let me start with a direct question about content moderation policies.

MR. ZUCKERBERG: Thank you, Chairman Johnson. I appreciate the opportunity to discuss these important issues with the committee.

CHAIRMAN JOHNSON: According to the 2023 Pew Research study on social media usage, 72% of Americans get their news from social media platforms. How do you ensure the accuracy of information on your platform?

MR. ZUCKERBERG: We have invested heavily in fact-checking partnerships and AI systems to identify and reduce the spread of misinformation. We work with over 80 independent fact-checking organizations globally.

REP. SMITH: Mr. Zuckerberg, the GAO report from last year clearly states that platform oversight mechanisms are insufficient. What specific steps are you taking to address these concerns?

MR. ZUCKERBERG: We've implemented several new measures, including enhanced transparency reports and improved appeals processes. As outlined in the CRS report on Section 230, we believe in balanced approaches that protect both free speech and user safety.

REP. MARTINEZ: Mr. Musk, your acquisition of Twitter has led to significant changes in content moderation. Can you explain your philosophy?

MR. MUSK: Our approach is based on maximizing free speech within the bounds of the law. We've reduced content restrictions while maintaining policies against illegal content.

REP. DAVIS: Ms. Yaccarino, how does your platform handle misinformation during election periods?

MS. YACCARINO: We have specialized teams that work around the clock during election periods, partnering with election officials and implementing additional verification measures for election-related content.
  `,
}

export default function TranscriptView({ params }: { params: { id: string } }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCitation, setSelectedCitation] = useState<number | null>(null)

  const highlightSearchTerm = (text: string, term: string) => {
    if (!term) return text
    const regex = new RegExp(`(${term})`, "gi")
    return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>')
  }

  const filteredCitations = transcriptData.citations.filter(
    (citation) =>
      citation.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      citation.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      citation.speaker.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/historical">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Historical Hearings
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-balance">{transcriptData.title}</h1>
          <p className="text-muted-foreground mt-2">Transcript and Citation Analysis</p>
        </div>
      </div>

      {/* Header Info */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{transcriptData.committee}</CardTitle>
              <CardDescription className="mt-2">
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {new Date(transcriptData.date).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    {transcriptData.pages} pages
                  </div>
                  <div className="flex items-center gap-2">
                    <ExternalLink className="h-4 w-4" />
                    {transcriptData.citations.length} citations
                  </div>
                </div>
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Download PDF
              </Button>
              <Button variant="outline" size="sm">
                <LinkIcon className="mr-2 h-4 w-4" />
                Share
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div>
            <h4 className="text-sm font-medium mb-2">Witnesses:</h4>
            <div className="flex flex-wrap gap-2">
              {transcriptData.witnesses.map((witness, index) => (
                <Badge key={index} variant="secondary">
                  <Users className="mr-1 h-3 w-3" />
                  {witness}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Citations Panel */}
        <div className="lg:col-span-1">
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Quote className="h-5 w-5" />
                Citations & References
              </CardTitle>
              <CardDescription>Documents and sources referenced in the hearing</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Input
                  placeholder="Search citations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />

                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {filteredCitations.map((citation) => (
                      <div
                        key={citation.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedCitation === citation.id
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        }`}
                        onClick={() => setSelectedCitation(citation.id)}
                      >
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <Badge variant="outline" className="text-xs">
                              Page {citation.page}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {citation.speaker}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">{citation.text}</p>
                          <div className="flex items-center gap-2">
                            <ExternalLink className="h-3 w-3 text-muted-foreground" />
                            <span className="text-xs font-medium">{citation.source}</span>
                          </div>
                          <Button variant="ghost" size="sm" className="w-full text-xs">
                            <FileText className="mr-1 h-3 w-3" />
                            View Document
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Transcript */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Full Transcript
              </CardTitle>
              <div className="flex items-center gap-4">
                <Input
                  placeholder="Search transcript..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
                <Badge variant="outline">{transcriptData.pages} pages</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div
                  className="prose prose-sm max-w-none whitespace-pre-line"
                  dangerouslySetInnerHTML={{
                    __html: highlightSearchTerm(transcriptData.transcript, searchTerm),
                  }}
                />
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
