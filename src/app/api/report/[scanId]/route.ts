import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

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

export async function GET(
  request: NextRequest,
  { params }: { params: { scanId: string } }
) {
  try {
    const { scanId } = params
    
    if (!scanId) {
      return NextResponse.json(
        { error: 'Scan ID is required' },
        { status: 400 }
      )
    }
    
    // Fetch report from database
    const report = await db.scanReport.findUnique({
      where: {
        scanId: scanId
      }
    })
    
    if (!report) {
      return NextResponse.json(
        { error: 'Report not found' },
        { status: 404 }
      )
    }
    
    // Parse the results JSON and format the response
    const results: VerificationResult[] = JSON.parse(report.results)
    
    const formattedReport: FreshnessReport = {
      scanId: report.scanId,
      url: report.url,
      title: report.title,
      freshnessScore: report.freshnessScore,
      totalSnippets: report.totalSnippets,
      verifiedSnippets: report.verifiedSnippets,
      outdatedSnippets: report.outdatedSnippets,
      results,
      scanDate: report.scanDate.toISOString()
    }
    
    return NextResponse.json(formattedReport)
    
  } catch (error) {
    console.error('Error fetching report:', error)
    return NextResponse.json(
      { error: 'Failed to fetch report' },
      { status: 500 }
    )
  }
}