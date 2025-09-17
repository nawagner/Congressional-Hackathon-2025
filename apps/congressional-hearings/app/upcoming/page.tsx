"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar, Clock, MapPin, Users, FileText, Plus, Filter } from "lucide-react"
import Link from "next/link"

// Mock data for upcoming hearings
const upcomingHearings = [
  {
    id: 1,
    title: "Oversight of Federal AI Regulation",
    committee: "House Committee on Science, Space, and Technology",
    date: "2024-01-15",
    time: "10:00 AM",
    location: "Rayburn House Office Building, Room 2318",
    status: "scheduled",
    witnesses: ["Dr. Sarah Chen", "Prof. Michael Rodriguez", "Janet Williams"],
    prepSheetStatus: "in-progress",
    relatedDocs: 12,
    priority: "high",
  },
  {
    id: 2,
    title: "Banking Sector Cybersecurity Measures",
    committee: "Senate Committee on Banking, Housing, and Urban Affairs",
    date: "2024-01-18",
    time: "2:30 PM",
    location: "Hart Senate Office Building, Room 538",
    status: "confirmed",
    witnesses: ["Robert Kim", "Lisa Thompson", "David Park"],
    prepSheetStatus: "completed",
    relatedDocs: 8,
    priority: "medium",
  },
  {
    id: 3,
    title: "Climate Change Impact on Agriculture",
    committee: "House Committee on Agriculture",
    date: "2024-01-22",
    time: "9:00 AM",
    location: "Longworth House Office Building, Room 1300",
    status: "tentative",
    witnesses: ["Dr. Amanda Foster", "John Martinez"],
    prepSheetStatus: "not-started",
    relatedDocs: 15,
    priority: "high",
  },
  {
    id: 4,
    title: "Healthcare Data Privacy Standards",
    committee: "Senate Committee on Health, Education, Labor and Pensions",
    date: "2024-01-25",
    time: "11:00 AM",
    location: "Dirksen Senate Office Building, Room 430",
    status: "scheduled",
    witnesses: ["Dr. Patricia Lee", "Mark Johnson", "Susan Davis"],
    prepSheetStatus: "in-progress",
    relatedDocs: 6,
    priority: "medium",
  },
]

const committees = [
  "All Committees",
  "House Committee on Science, Space, and Technology",
  "Senate Committee on Banking, Housing, and Urban Affairs",
  "House Committee on Agriculture",
  "Senate Committee on Health, Education, Labor and Pensions",
]

export default function UpcomingHearings() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCommittee, setSelectedCommittee] = useState("All Committees")
  const [selectedPriority, setSelectedPriority] = useState("all")

  const filteredHearings = upcomingHearings.filter((hearing) => {
    const matchesSearch =
      hearing.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hearing.committee.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCommittee = selectedCommittee === "All Committees" || hearing.committee === selectedCommittee
    const matchesPriority = selectedPriority === "all" || hearing.priority === selectedPriority

    return matchesSearch && matchesCommittee && matchesPriority
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-100 text-green-800 border-green-200"
      case "scheduled":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "tentative":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getPrepStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200"
      case "in-progress":
        return "bg-orange-100 text-orange-800 border-orange-200"
      case "not-started":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200"
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "low":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-balance">Upcoming Hearings</h1>
          <p className="text-muted-foreground mt-2">Manage and prepare for upcoming committee hearings</p>
        </div>
        <Button asChild>
          <Link href="/prep-sheets/new">
            <Plus className="mr-2 h-4 w-4" />
            New Prep Sheet
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Search hearings..."
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
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <Select value={selectedPriority} onValueChange={setSelectedPriority}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm("")
                  setSelectedCommittee("All Committees")
                  setSelectedPriority("all")
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
                  <CardDescription className="text-sm">{hearing.committee}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge className={getPriorityColor(hearing.priority)}>{hearing.priority} priority</Badge>
                  <Badge className={getStatusColor(hearing.status)}>{hearing.status}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{new Date(hearing.date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.time}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.location}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{hearing.witnesses.length} witnesses</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Prep Sheet:</span>
                      <Badge className={getPrepStatusColor(hearing.prepSheetStatus)}>
                        {hearing.prepSheetStatus.replace("-", " ")}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">{hearing.relatedDocs} related documents</div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/hearings/${hearing.id}`}>View Details</Link>
                    </Button>
                    <Button size="sm" asChild>
                      <Link href={`/prep-sheets/${hearing.id}`}>
                        {hearing.prepSheetStatus === "not-started" ? "Start Prep" : "Edit Prep"}
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>

              {/* Witnesses */}
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Witnesses:</h4>
                <div className="flex flex-wrap gap-2">
                  {hearing.witnesses.map((witness, index) => (
                    <Badge key={index} variant="secondary">
                      {witness}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredHearings.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No hearings found</h3>
            <p className="text-muted-foreground">Try adjusting your filters or search terms.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
