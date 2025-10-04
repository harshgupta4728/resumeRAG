import React, { useState } from 'react'
import { Search as SearchIcon, FileText, Star } from 'lucide-react'
import apiClient from '../api/client'

const Search = () => {
  const [query, setQuery] = useState('')
  const [k, setK] = useState(3)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError('')
    setResults([])

    try {
      const response = await apiClient.post('/ask', {
        query: query.trim(),
        k: k
      })

      setResults(response.data.results)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search Resumes</h1>
        <p className="mt-1 text-sm text-gray-600">
          Ask questions about the uploaded resumes using natural language
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex space-x-4">
          <div className="flex-1">
            <label htmlFor="query" className="sr-only">
              Search query
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <SearchIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="query"
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="e.g., Who has experience with FastAPI?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="w-24">
            <label htmlFor="k" className="sr-only">
              Number of results
            </label>
            <input
              type="number"
              id="k"
              min="1"
              max="10"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              value={k}
              onChange={(e) => setK(parseInt(e.target.value) || 3)}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium text-gray-900">
            Search Results ({results.length})
          </h2>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">
                      {result.filename}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-400 fill-current" />
                    <span className="text-sm text-gray-600">
                      {(result.similarity_score * 100).toFixed(1)}% match
                    </span>
                  </div>
                </div>
                <div className="prose prose-sm max-w-none">
                  <p className="text-gray-700 leading-relaxed">
                    {result.content}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && results.length === 0 && query && (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search query or upload more resumes.
          </p>
        </div>
      )}

      {/* Example Queries */}
      {!query && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Example Queries:</h3>
          <div className="text-sm text-blue-700 space-y-1">
            <div>• "Who has experience with Python?"</div>
            <div>• "Find candidates with machine learning skills"</div>
            <div>• "Show me resumes with React experience"</div>
            <div>• "Who has worked with databases?"</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Search
