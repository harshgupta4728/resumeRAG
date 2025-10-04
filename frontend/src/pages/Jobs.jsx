import React, { useState, useEffect } from 'react'
import { Plus, Search, FileText, Star, AlertCircle, CheckCircle } from 'lucide-react'
import apiClient from '../api/client'

const Jobs = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newJob, setNewJob] = useState({ title: '', description: '' })
  const [matching, setMatching] = useState({})
  const [matches, setMatches] = useState({})

  // Load jobs on component mount
  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      // Since we don't have a GET /jobs endpoint, we'll create some mock data
      // In a real app, you'd call: const response = await apiClient.get('/jobs')
      setJobs([])
    } catch (err) {
      setError('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const createJob = async (e) => {
    e.preventDefault()
    if (!newJob.title.trim() || !newJob.description.trim()) return

    setLoading(true)
    try {
      const response = await apiClient.post('/jobs', newJob)
      setJobs(prev => [...prev, response.data])
      setNewJob({ title: '', description: '' })
      setShowCreateForm(false)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  const matchCandidates = async (jobId, topN = 5) => {
    setMatching(prev => ({ ...prev, [jobId]: true }))
    try {
      const response = await apiClient.post(`/jobs/${jobId}/match`, { top_n: topN })
      setMatches(prev => ({ ...prev, [jobId]: response.data }))
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Matching failed')
    } finally {
      setMatching(prev => ({ ...prev, [jobId]: false }))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Management</h1>
          <p className="mt-1 text-sm text-gray-600">
            Create job descriptions and match candidates
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Job
        </button>
      </div>

      {/* Create Job Form */}
      {showCreateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Job</h2>
          <form onSubmit={createJob} className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Job Title
              </label>
              <input
                type="text"
                id="title"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={newJob.title}
                onChange={(e) => setNewJob(prev => ({ ...prev, title: e.target.value }))}
                placeholder="e.g., Senior Python Developer"
                required
              />
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Job Description
              </label>
              <textarea
                id="description"
                rows={6}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={newJob.description}
                onChange={(e) => setNewJob(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the role, requirements, and responsibilities..."
                required
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Job'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Jobs List */}
      <div className="space-y-4">
        {jobs.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs created</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first job description.
            </p>
          </div>
        ) : (
          jobs.map((job) => (
            <div key={job.id} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{job.title}</h3>
                  <p className="text-sm text-gray-500">
                    Created {new Date(job.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => matchCandidates(job.id)}
                  disabled={matching[job.id]}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Search className="h-4 w-4 mr-2" />
                  {matching[job.id] ? 'Matching...' : 'Match Candidates'}
                </button>
              </div>
              
              <div className="prose prose-sm max-w-none mb-4">
                <p className="text-gray-700">{job.description}</p>
              </div>

              {/* Match Results */}
              {matches[job.id] && (
                <div className="mt-6 border-t pt-6">
                  <h4 className="text-md font-medium text-gray-900 mb-4">
                    Top Matches ({matches[job.id].matches.length})
                  </h4>
                  <div className="space-y-3">
                    {matches[job.id].matches.map((match, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <FileText className="h-4 w-4 text-gray-400" />
                            <span className="text-sm font-medium text-gray-900">
                              {match.filename}
                            </span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Star className="h-4 w-4 text-yellow-400 fill-current" />
                            <span className="text-sm text-gray-600">
                              {(match.similarity_score * 100).toFixed(1)}% match
                            </span>
                          </div>
                        </div>
                        
                        {match.evidence && (
                          <div className="mb-3">
                            <h5 className="text-xs font-medium text-gray-700 mb-1">Evidence:</h5>
                            <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                              {match.evidence}
                            </p>
                          </div>
                        )}

                        {match.missing_requirements && match.missing_requirements.length > 0 && (
                          <div>
                            <h5 className="text-xs font-medium text-gray-700 mb-1 flex items-center">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Missing Requirements:
                            </h5>
                            <ul className="text-xs text-gray-600 space-y-1">
                              {match.missing_requirements.map((req, reqIndex) => (
                                <li key={reqIndex} className="flex items-start">
                                  <span className="text-red-500 mr-1">•</span>
                                  {req}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Jobs
