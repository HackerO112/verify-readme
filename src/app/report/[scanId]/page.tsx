'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  ArrowLeft, 
  ExternalLink,
  Copy,
  Share
} from 'lucide-react'

interface VerificationResult {
  snippetId: string
  status: 'verified' | 'outdated' | 'error'
  output?: string
  error?: string
  executionTime: number
}

interface FreshnessReport {
  scanId: string
  url: string
  title: string
  freshnessScore: number
  totalSnippets: number
  verifiedSnippets: number
  outdatedSnippets: number
  results: VerificationResult[]
  scanDate: string
}

export default function ReportPage() {
  const params = useParams()
  const router = useRouter()
  const scanId = params.scanId as string
  const [report, setReport] = useState<FreshnessReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadReport = async () => {
      try {
        setIsLoading(true)
        
        const response = await fetch(`/api/report/${scanId}`)
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to load report')
        }
        
        const reportData = await response.json()
        setReport(reportData)
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report')
      } finally {
        setIsLoading(false)
      }
    }

    loadReport()
  }, [scanId])

  const getStatusBadge = (status: VerificationResult['status']) => {
    switch (status) {
      case 'verified':
        return (
          <Badge className="bg-green-500 hover:bg-green-600">
            <CheckCircle className="w-3 h-3 mr-1" />
            Verified
          </Badge>
        )
      case 'outdated':
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            Outdated
          </Badge>
        )
      case 'error':
        return (
          <Badge variant="secondary" className="bg-yellow-500 hover:bg-yellow-600">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Error
          </Badge>
        )
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const copyReportUrl = () => {
    const url = window.location.href
    navigator.clipboard.writeText(url)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-muted-foreground">Loading report...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              {error || 'Report not found'}
            </p>
            <Button onClick={() => router.push('/')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button variant="ghost" onClick={() => router.push('/')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={copyReportUrl}>
              <Copy className="w-4 h-4 mr-2" />
              Copy Link
            </Button>
            <Button variant="outline" size="sm">
              <Share className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </div>

        {/* Report Header */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-2xl mb-2">{report.title}</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <ExternalLink className="w-4 h-4" />
                  <a 
                    href={report.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="hover:text-primary transition-colors"
                  >
                    {report.url}
                  </a>
                </CardDescription>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${getScoreColor(report.freshnessScore)}`}>
                  {report.freshnessScore}%
                </div>
                <p className="text-sm text-muted-foreground">Freshness Score</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-semibold text-green-600">{report.verifiedSnippets}</div>
                <p className="text-sm text-muted-foreground">Verified</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold text-red-600">{report.outdatedSnippets}</div>
                <p className="text-sm text-muted-foreground">Outdated</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold">{report.totalSnippets}</div>
                <p className="text-sm text-muted-foreground">Total Snippets</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold">
                  {new Date(report.scanDate).toLocaleDateString()}
                </div>
                <p className="text-sm text-muted-foreground">Scanned</p>
              </div>
            </div>
            <Progress value={report.freshnessScore} className="h-3" />
          </CardContent>
        </Card>

        {/* Code Snippets Results */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Code Verification Results</h2>
          
          {report.results.map((result, index) => (
            <Card key={result.snippetId}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Snippet #{index + 1}</CardTitle>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(result.status)}
                    <Badge variant="outline">
                      {result.executionTime}ms
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Mock code snippet display */}
                <div className="mb-4">
                  <pre className="text-sm bg-muted/50 p-4 rounded-lg overflow-x-auto">
                    <code>
                      {result.snippetId === '1' && `const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});`}
                      {result.snippetId === '2' && `app.use(bodyParser());`}
                      {result.snippetId === '3' && `const { MongoClient } = require('mongodb');

async function connect() {
  const client = new MongoClient('mongodb://localhost:27017');
  await client.connect();
  return client;
}`}
                    </code>
                  </pre>
                </div>
                
                {result.status === 'verified' && result.output && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800 font-medium mb-1">Output:</p>
                    <p className="text-sm text-green-700">{result.output}</p>
                  </div>
                )}
                
                {result.status === 'outdated' && result.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800 font-medium mb-1">Error:</p>
                    <p className="text-sm text-red-700">{result.error}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Scan completed on {new Date(report.scanDate).toLocaleString()}
            </div>
            <div>
              Report ID: {report.scanId}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}