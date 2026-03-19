'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  clearToken,
  getSavedUsername,
  getRecentResults,
  isAuthenticated,
  screenResumes,
} from '@/lib/api';
import { ScreeningResult } from '@/types';
import CandidateCard from '@/components/CandidateCard';
import ResultsTable from '@/components/ResultsTable';
import Analytics from '@/components/Analytics';
import FilterPanel from '@/components/FilterPanel';

type Tab = 'screen' | 'recent';

export default function DashboardPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [tab, setTab] = useState<Tab>('screen');

  // Upload state
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const jdRef = useRef<HTMLInputElement>(null);
  const resumesRef = useRef<HTMLInputElement>(null);

  // Results state
  const [results, setResults] = useState<ScreeningResult[]>([]);
  const [filtered, setFiltered] = useState<ScreeningResult[]>([]);
  const [screening, setScreening] = useState(false);
  const [screenError, setScreenError] = useState('');
  const [jdDomain, setJdDomain] = useState('');
  const [jdSeniority, setJdSeniority] = useState('');

  // Recent
  const [recent, setRecent] = useState<ScreeningResult[]>([]);
  const [recentLoading, setRecentLoading] = useState(false);

  // View toggle inside results
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }
    setUsername(getSavedUsername() || '');
  }, [router]);

  function handleSignOut() {
    clearToken();
    router.push('/login');
  }

  async function handleScreen() {
    if (!jdFile || resumeFiles.length === 0) return;
    setScreening(true);
    setScreenError('');
    setResults([]);
    setFiltered([]);
    try {
      const data = await screenResumes(jdFile, resumeFiles);
      setResults(data.results);
      setFiltered(data.results);
      if (data.results.length > 0) {
        setJdDomain(data.results[0].jd_domain || '');
        setJdSeniority(data.results[0].jd_seniority || '');
      }
    } catch (err: unknown) {
      setScreenError(err instanceof Error ? err.message : 'Screening failed');
    } finally {
      setScreening(false);
    }
  }

  async function loadRecent() {
    setRecentLoading(true);
    try {
      const data = await getRecentResults(30);
      setRecent(data);
    } catch {
      setRecent([]);
    } finally {
      setRecentLoading(false);
    }
  }

  function handleTabChange(t: Tab) {
    setTab(t);
    if (t === 'recent' && recent.length === 0) loadRecent();
  }

  // CSV download
  function downloadCSV() {
    if (!results.length) return;
    const cols = [
      'resume_filename', 'similarity_score', 'full_name', 'university_name',
      'email_id', 'location', 'total_experience', 'analysis_depth',
      'overall_recommendation', 'jd_domain', 'jd_seniority',
    ];
    const header = cols.join(',');
    const rows = results.map((r) =>
      cols.map((c) => JSON.stringify((r as unknown as Record<string, unknown>)[c] ?? '')).join(',')
    );
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'screening_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  const avgScore = results.length
    ? results.reduce((s, r) => s + r.similarity_score, 0) / results.length
    : 0;
  const topScore = results.length ? Math.max(...results.map((r) => r.similarity_score)) : 0;
  const highMatchCount = results.filter((r) => r.similarity_score >= 0.7).length;
  const deepCount = results.filter((r) => r.analysis_depth === 'deep').length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🎯</span>
          <span className="text-xl font-bold text-gray-900">FitFindr</span>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium ml-1">
            LangGraph
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">👤 {username}</span>
          <button
            onClick={handleSignOut}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Sign Out
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit mb-6">
          {(['screen', 'recent'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => handleTabChange(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t === 'screen' ? '🔍 Screen Resumes' : '📜 Recent Screenings'}
            </button>
          ))}
        </div>

        {/* ── Screen tab ───────────────────────────────────────────────────── */}
        {tab === 'screen' && (
          <div className="space-y-6">
            {/* Upload card */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📤 Upload Documents</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* JD */}
                <div
                  onClick={() => jdRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 hover:border-blue-400 rounded-lg p-6 text-center cursor-pointer transition-colors"
                >
                  <div className="text-3xl mb-2">📄</div>
                  <p className="font-medium text-gray-700">
                    {jdFile ? jdFile.name : 'Job Description'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">PDF or TXT</p>
                  <input
                    ref={jdRef}
                    type="file"
                    accept=".pdf,.txt"
                    className="hidden"
                    onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
                  />
                </div>

                {/* Resumes */}
                <div
                  onClick={() => resumesRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 hover:border-blue-400 rounded-lg p-6 text-center cursor-pointer transition-colors"
                >
                  <div className="text-3xl mb-2">📚</div>
                  <p className="font-medium text-gray-700">
                    {resumeFiles.length > 0
                      ? `${resumeFiles.length} resume${resumeFiles.length > 1 ? 's' : ''} selected`
                      : 'Resumes'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">PDF or TXT · multiple allowed</p>
                  <input
                    ref={resumesRef}
                    type="file"
                    accept=".pdf,.txt"
                    multiple
                    className="hidden"
                    onChange={(e) =>
                      setResumeFiles(e.target.files ? Array.from(e.target.files) : [])
                    }
                  />
                </div>
              </div>

              {screenError && (
                <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {screenError}
                </div>
              )}

              <button
                onClick={handleScreen}
                disabled={!jdFile || resumeFiles.length === 0 || screening}
                className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {screening ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Analysing resumes…
                  </>
                ) : (
                  '🚀 Screen Resumes'
                )}
              </button>
            </div>

            {/* Results */}
            {results.length > 0 && (
              <>
                {/* JD insights banner */}
                {(jdDomain !== 'N/A' || jdSeniority !== 'N/A') && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-xl px-5 py-3 flex flex-wrap gap-4 text-sm">
                    <span className="font-semibold text-indigo-800">📋 JD Analysis:</span>
                    {jdDomain !== 'N/A' && (
                      <span className="text-indigo-700">Domain: <strong>{jdDomain}</strong></span>
                    )}
                    {jdSeniority !== 'N/A' && (
                      <span className="text-indigo-700">Seniority: <strong>{jdSeniority}</strong></span>
                    )}
                  </div>
                )}

                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Total Resumes', value: results.length, icon: '📊' },
                    { label: 'Avg. Match', value: `${(avgScore * 100).toFixed(1)}%`, icon: '📈' },
                    { label: 'Top Match', value: `${(topScore * 100).toFixed(1)}%`, icon: '⭐' },
                    { label: 'Deep Analysis', value: `${deepCount} candidates`, icon: '🔬' },
                  ].map(({ label, value, icon }) => (
                    <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
                      <div className="text-2xl mb-1">{icon}</div>
                      <div className="text-2xl font-bold text-gray-900">{value}</div>
                      <div className="text-xs text-gray-500">{label}</div>
                    </div>
                  ))}
                </div>

                {/* High match badge */}
                {highMatchCount > 0 && (
                  <div className="bg-green-50 border border-green-200 text-green-800 text-sm px-4 py-2 rounded-lg">
                    ✅ <strong>{highMatchCount}</strong> candidate{highMatchCount > 1 ? 's' : ''} with &gt;70% match score
                  </div>
                )}

                {/* Filter */}
                <FilterPanel results={results} onFilter={setFiltered} />

                {/* View toggle + download */}
                <div className="flex items-center justify-between">
                  <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
                    <button
                      onClick={() => setViewMode('cards')}
                      className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${viewMode === 'cards' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'}`}
                    >
                      Cards
                    </button>
                    <button
                      onClick={() => setViewMode('table')}
                      className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'}`}
                    >
                      Table
                    </button>
                  </div>
                  <button
                    onClick={downloadCSV}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    📥 Download CSV
                  </button>
                </div>

                {viewMode === 'cards' ? (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-500">
                      Showing {filtered.length} of {results.length} candidates
                    </p>
                    {filtered.map((r, i) => (
                      <CandidateCard key={r.resume_filename} rank={i + 1} result={r} />
                    ))}
                  </div>
                ) : (
                  <ResultsTable results={filtered} />
                )}

                {/* Analytics */}
                <Analytics results={results} />
              </>
            )}

            {/* Welcome state */}
            {!screening && results.length === 0 && !screenError && (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
                <div className="text-5xl mb-4">👋</div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Welcome to FitFindr</h3>
                <p className="text-sm">
                  Upload a job description and one or more resumes above, then click{' '}
                  <strong>Screen Resumes</strong> to start.
                </p>
                <div className="mt-4 text-xs text-gray-400">
                  Powered by BERT · Groq LLaMA 3 · LangGraph · LangSmith
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Recent tab ─────────────────────────────────────────────────── */}
        {tab === 'recent' && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">📜 Recent Screenings</h2>
            {recentLoading ? (
              <div className="text-center py-8 text-gray-400">Loading…</div>
            ) : recent.length === 0 ? (
              <div className="text-center py-8 text-gray-400">No recent screenings found.</div>
            ) : (
              <ResultsTable results={recent} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
