'use client';
import { useState } from 'react';
import { ScreeningResult } from '@/types';

const RECOMMENDATION_STYLE: Record<string, string> = {
  'Strong Recommend': 'bg-green-100 text-green-800',
  Recommend: 'bg-blue-100 text-blue-800',
  Maybe: 'bg-yellow-100 text-yellow-800',
  Pass: 'bg-red-100 text-red-800',
};

const DEPTH_STYLE: Record<string, string> = {
  deep: 'bg-purple-100 text-purple-800',
  standard: 'bg-blue-100 text-blue-700',
  skip: 'bg-gray-100 text-gray-600',
};

function ScoreBadge({ score }: { score: number }) {
  const pct = score * 100;
  const color =
    pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-400';
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-semibold text-gray-700">{pct.toFixed(1)}%</span>
    </div>
  );
}

export default function CandidateCard({
  rank,
  result: r,
}: {
  rank: number;
  result: ScreeningResult;
}) {
  const [open, setOpen] = useState(rank === 1);

  const recStyle =
    RECOMMENDATION_STYLE[r.overall_recommendation] ?? 'bg-gray-100 text-gray-600';
  const depthStyle = DEPTH_STYLE[r.analysis_depth] ?? 'bg-gray-100 text-gray-600';

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header — always visible */}
      <button
        className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center flex-shrink-0">
            {rank}
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">{r.full_name}</p>
            <p className="text-xs text-gray-400 truncate">{r.resume_filename}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0 ml-4">
          <ScoreBadge score={r.similarity_score} />
          {r.overall_recommendation !== 'N/A' && (
            <span className={`text-xs px-2 py-1 rounded-full font-medium hidden sm:block ${recStyle}`}>
              {r.overall_recommendation}
            </span>
          )}
          <span className={`text-xs px-2 py-1 rounded-full font-medium hidden sm:block ${depthStyle}`}>
            {r.analysis_depth}
          </span>
          <span className="text-gray-400">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Body */}
      {open && (
        <div className="px-5 pb-5 border-t border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
            {/* Contact & basics */}
            <div className="space-y-2 text-sm">
              <h4 className="font-semibold text-gray-700 mb-2">📋 Profile</h4>
              {[
                { label: '🎓 University', value: `${r.university_name} (${r.national_or_international})` },
                { label: '📧 Email', value: r.email_id },
                { label: '� Phone', value: r.phone_number },
                { label: '�🔗 GitHub', value: r.github_link },
                { label: '📍 Location', value: r.location },
                { label: '💼 Experience', value: r.total_experience },
              ].map(({ label, value }) =>
                value && value !== 'N/A' ? (
                  <div key={label}>
                    <span className="text-gray-500">{label}: </span>
                    {label === '🔗 GitHub' && value !== 'N/A' ? (
                      <a href={value} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all">
                        {value}
                      </a>
                    ) : (
                      <span className="text-gray-900">{value}</span>
                    )}
                  </div>
                ) : null
              )}
              {r.company_names.length > 0 && (
                <div>
                  <span className="text-gray-500">🏢 Companies: </span>
                  <span className="text-gray-900">{r.company_names.join(', ')}</span>
                </div>
              )}
            </div>

            {/* Skills */}
            <div className="space-y-3 text-sm">
              <h4 className="font-semibold text-gray-700">🛠️ Skills</h4>
              {r.technical_skills.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Technical</p>
                  <div className="flex flex-wrap gap-1">
                    {r.technical_skills.slice(0, 12).map((s) => (
                      <span key={s} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {r.soft_skills.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Soft</p>
                  <div className="flex flex-wrap gap-1">
                    {r.soft_skills.slice(0, 8).map((s) => (
                      <span key={s} className="bg-purple-50 text-purple-700 text-xs px-2 py-0.5 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Deep analysis — only when analysis_depth === 'deep' */}
            {r.analysis_depth === 'deep' && (
              <div className="space-y-3 text-sm">
                <h4 className="font-semibold text-gray-700">🔬 Deep Analysis</h4>

                {r.overall_recommendation !== 'N/A' && (
                  <div>
                    <span className="text-gray-500 text-xs">Recommendation</span>
                    <div className="mt-1">
                      <span className={`text-xs px-2 py-1 rounded-full font-semibold ${recStyle}`}>
                        {r.overall_recommendation}
                      </span>
                    </div>
                  </div>
                )}

                {r.skill_gaps.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">⚠️ Skill Gaps</p>
                    <ul className="space-y-0.5">
                      {r.skill_gaps.map((g) => (
                        <li key={g} className="text-orange-700 text-xs flex gap-1">
                          <span>•</span>{g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {r.red_flags.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">🚩 Red Flags</p>
                    <ul className="space-y-0.5">
                      {r.red_flags.map((f) => (
                        <li key={f} className="text-red-600 text-xs flex gap-1">
                          <span>•</span>{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {r.interview_questions.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">❓ Interview Questions</p>
                    <ol className="space-y-1">
                      {r.interview_questions.map((q, i) => (
                        <li key={i} className="text-gray-700 text-xs">
                          {i + 1}. {q}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
