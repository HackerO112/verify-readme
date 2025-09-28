'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, Link, CheckCircle, XCircle, Clock } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function Home() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    try {
      new URL(url)
    } catch {
      setError('Please enter a valid URL')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to scan URL')
      }

      const report = await response.json()
      
      // Show cache notification if applicable
      if (report.fromCache) {
        toast({
          title: "Report loaded from cache",
          description: "Showing results from recent scan of this URL",
        })
      } else {
        toast({
          title: "Scan completed successfully",
          description: "Generated fresh verification report",
        })
      }
      
      // Redirect to report page
      window.location.href = `/report/${report.scanId}`
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan URL. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-primary-foreground" />
              </div>
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            VeriCode
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            The live documentation verifier that fights "documentation rot" by checking if code snippets from tutorials still work with the latest dependencies.
          </p>

          {/* URL Input Form */}
          <Card className="max-w-2xl mx-auto mb-12">
            <CardHeader>
              <CardTitle className="text-2xl">Verify a Tutorial</CardTitle>
              <CardDescription>
                Paste a URL to any technical tutorial, blog post, or documentation page
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Link className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                    <Input
                      type="url"
                      placeholder="https://example.com/tutorial"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="pl-10"
                      disabled={isLoading}
                    />
                  </div>
                  <Button type="submit" disabled={isLoading} className="px-8">
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      'Verify'
                    )}
                  </Button>
                </div>
                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                Live Validation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Code snippets are executed against the latest stable versions of dependencies in a secure sandbox.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-500" />
                Error Detection
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Get exact error messages when code fails, showing you exactly why it's outdated.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-500" />
                Community Cache
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Results are cached so popular tutorials are only scanned once, providing instant results.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Example Report Preview */}
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>Sample Freshness Report</CardTitle>
            <CardDescription>
              See what a verification report looks like
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold">Overall Freshness Score</span>
                <Badge variant="secondary" className="text-lg px-3 py-1">
                  75%
                </Badge>
              </div>
              
              <div className="space-y-3">
                <div className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <Badge className="bg-green-500 hover:bg-green-600">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Verified
                    </Badge>
                    <code className="text-sm bg-muted px-2 py-1 rounded">JavaScript</code>
                  </div>
                  <pre className="text-sm bg-muted/50 p-3 rounded overflow-x-auto">
                    <code>console.log('Hello, World!');</code>
                  </pre>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <Badge variant="destructive">
                      <XCircle className="w-3 h-3 mr-1" />
                      Outdated
                    </Badge>
                    <code className="text-sm bg-muted px-2 py-1 rounded">Express.js</code>
                  </div>
                  <pre className="text-sm bg-muted/50 p-3 rounded overflow-x-auto">
                    <code>app.use(bodyParser());</code>
                  </pre>
                  <p className="text-sm text-destructive mt-2">
                    TypeError: app.use(bodyParser()) is not a function
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}