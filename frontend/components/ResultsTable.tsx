'use client';
import { useState } from 'react';
import { ScreeningResult } from '@/types';

const REC_COLOR: Record<string, string> = {
  'Strong Recommend': 'text-green-700',
  Recommend: 'text-blue-700',
  Maybe: 'text-yellow-700',
  Pass: 'text-red-600',
};

type SortKey = 'similarity_score' | 'full_name' | 'total_experience' | 'overall_recommendation';

export default function ResultsTable({ results }: { results: ScreeningResult[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('similarity_score');
  const [sortAsc, setSortAsc] = useState(false);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((a) => !a);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  const sorted = [...results].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    if (typeof av === 'number' && typeof bv === 'number')
      return sortAsc ? av - bv : bv - av;
    return sortAsc
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  function SortBtn({ k, label }: { k: SortKey; label: string }) {
    return (
      <button
        onClick={() => toggleSort(k)}
        className="flex items-center gap-1 text-xs font-semibold text-left hover:text-blue-600"
      >
        {label}
        {sortKey === k ? (sortAsc ? ' ▲' : ' ▼') : ' ↕'}
      </button>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left">#</th>
            <th className="px-4 py-3 text-left">
              <SortBtn k="full_name" label="Name" />
            </th>
            <th className="px-4 py-3 text-left">
              <SortBtn k="similarity_score" label="Match %" />
            </th>
            <th className="px-4 py-3 text-left hidden md:table-cell">University</th>
            <th className="px-4 py-3 text-left hidden md:table-cell">
              <SortBtn k="total_experience" label="Experience" />
            </th>
            <th className="px-4 py-3 text-left hidden lg:table-cell">Location</th>
            <th className="px-4 py-3 text-left hidden lg:table-cell">Depth</th>
            <th className="px-4 py-3 text-left">
              <SortBtn k="overall_recommendation" label="Recommendation" />
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.map((r, i) => (
            <tr key={`${r.resume_filename}-${i}`} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-500">{i + 1}</td>
              <td className="px-4 py-3 font-medium text-gray-900 max-w-[160px] truncate">
                {r.full_name}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-16 bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        r.similarity_score >= 0.7
                          ? 'bg-green-500'
                          : r.similarity_score >= 0.4
                          ? 'bg-yellow-500'
                          : 'bg-red-400'
                      }`}
                      style={{ width: `${r.similarity_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-gray-700">
                    {(r.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 hidden md:table-cell text-gray-600 max-w-[140px] truncate">
                {r.university_name}
              </td>
              <td className="px-4 py-3 hidden md:table-cell text-gray-600">{r.total_experience}</td>
              <td className="px-4 py-3 hidden lg:table-cell text-gray-600">{r.location}</td>
              <td className="px-4 py-3 hidden lg:table-cell">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    r.analysis_depth === 'deep'
                      ? 'bg-purple-100 text-purple-700'
                      : r.analysis_depth === 'standard'
                      ? 'bg-blue-50 text-blue-600'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {r.analysis_depth}
                </span>
              </td>
              <td className={`px-4 py-3 font-medium text-xs ${REC_COLOR[r.overall_recommendation] ?? 'text-gray-600'}`}>
                {r.overall_recommendation !== 'N/A' ? r.overall_recommendation : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
