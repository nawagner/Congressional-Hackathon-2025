"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileText, Plus, Search, Calendar, Users, Clock, Edit, Eye } from "lucide-react"
import Link from "next/link"

// Mock data for prep sheets
const prepSheets = [
  {
    id: 1,
    title: "AI Regulation Oversight - Prep Sheet",
    hearingTitle: "Oversight of Federal AI Regulation",
    committee: "House Science, Space, and Technology",
    date: "2024-01-15",
    status: "in-progress",
    lastModified: "2024-01-10",
    assignedTo: "Sarah Johnson",
    completionPercentage: 75,
    sections: {
      completed: 6,
      total: 8,
    },
    relatedDocs: 12,
    priority: "high",
  },
  {
    id: 2,
    title: "Banking Cybersecurity - Prep Sheet",
    hearingTitle: "Banking Sector Cybersecurity Measures",
    committee: "Senate Banking, Housing, and Urban Affairs",
    date: "2024-01-18",
    status: "completed",
    lastModified: "2024-01-08",
    assignedTo: "Michael Chen",
    completionPercentage: 100,
    sections: {
      completed: 7,
      total: 7,
    },
    relatedDocs: 8,
    priority: "medium",
  },
  {
    id: 3,
    title: "Climate Agriculture Impact - Prep Sheet",
    hearingTitle: "Climate Change Impact on Agriculture",
    committee: "House Agriculture",
    date: "2024-01-22",
    status: "not-started",
    lastModified: "2024-01-05",
    assignedTo: "Lisa Rodriguez",
    completionPercentage: 0,
    sections: {
      completed: 0,
      total: 9,
    },
    relatedDocs: 15,
    priority: "high",
  },
  {
    id: 4,
    title: "Healthcare Data Privacy - Prep Sheet",
    hearingTitle: "Healthcare Data Privacy Standards",
    committee: "Senate HELP Committee",
    date: "2024-01-25",
    status: "in-progress",
    lastModified: "2024-01-09",
    assignedTo: "David Park",
    completionPercentage: 45,
    sections: {
      completed: 3,
      total: 6,
    },
    relatedDocs: 6,
    priority: "medium",
  },
]

export default function PrepSheets() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [selectedPriority, setSelectedPriority] = useState("all")

  const filteredPrepSheets = prepSheets.filter((sheet) => {
    const matchesSearch =
      sheet.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sheet.hearingTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sheet.committee.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = selectedStatus === "all" || sheet.status === selectedStatus
    const matchesPriority = selectedPriority === "all" || sheet.priority === selectedPriority

    return matchesSearch && matchesStatus && matchesPriority
  })

  const getStatusColor = (status: string) => {
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
          <h1 className="text-3xl font-bold text-balance">Prep Sheets</h1>
          <p className="text-muted-foreground mt-2">Create and manage hearing preparation documents</p>
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
            <Search className="h-5 w-5" />
            Search & Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Search prep sheets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="not-started">Not Started</SelectItem>
                  <SelectItem value="in-progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
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
                  setSelectedStatus("all")
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

      {/* Prep Sheets Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredPrepSheets.map((sheet) => (
          <Card key={sheet.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-lg text-balance">{sheet.title}</CardTitle>
                  <CardDescription className="text-sm">{sheet.hearingTitle}</CardDescription>
                </div>
                <div className="flex flex-col gap-1">
                  <Badge className={getPriorityColor(sheet.priority)}>{sheet.priority}</Badge>
                  <Badge className={getStatusColor(sheet.status)}>{sheet.status.replace("-", " ")}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Progress</span>
                  <span>{sheet.completionPercentage}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${sheet.completionPercentage}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground">
                  {sheet.sections.completed} of {sheet.sections.total} sections completed
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>{new Date(sheet.date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{sheet.assignedTo}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span>{sheet.relatedDocs} docs</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>{new Date(sheet.lastModified).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="pt-2 border-t">
                <p className="text-sm text-muted-foreground mb-3">{sheet.committee}</p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild className="flex-1 bg-transparent">
                    <Link href={`/prep-sheets/${sheet.id}/view`}>
                      <Eye className="mr-1 h-3 w-3" />
                      View
                    </Link>
                  </Button>
                  <Button size="sm" asChild className="flex-1">
                    <Link href={`/prep-sheets/${sheet.id}/edit`}>
                      <Edit className="mr-1 h-3 w-3" />
                      Edit
                    </Link>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPrepSheets.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No prep sheets found</h3>
            <p className="text-muted-foreground mb-4">Try adjusting your filters or search terms.</p>
            <Button asChild>
              <Link href="/prep-sheets/new">Create New Prep Sheet</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
