'use client';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ScreeningResult } from '@/types';

function bucketScores(results: ScreeningResult[]) {
  const buckets: Record<string, number> = {
    '0–20%': 0, '20–40%': 0, '40–60%': 0, '60–80%': 0, '80–100%': 0,
  };
  results.forEach((r) => {
    const pct = r.similarity_score * 100;
    if (pct < 20) buckets['0–20%']++;
    else if (pct < 40) buckets['20–40%']++;
    else if (pct < 60) buckets['40–60%']++;
    else if (pct < 80) buckets['60–80%']++;
    else buckets['80–100%']++;
  });
  return Object.entries(buckets).map(([range, count]) => ({ range, count }));
}

function topUniversities(results: ScreeningResult[]) {
  const counts: Record<string, number> = {};
  results.forEach((r) => {
    if (r.university_name && r.university_name !== 'N/A') {
      counts[r.university_name] = (counts[r.university_name] ?? 0) + 1;
    }
  });
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({ name, count }));
}

function topSkills(results: ScreeningResult[]) {
  const counts: Record<string, number> = {};
  results.forEach((r) => {
    (r.technical_skills ?? []).forEach((s) => {
      counts[s] = (counts[s] ?? 0) + 1;
    });
  });
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([skill, count]) => ({ skill, count }));
}

const BUCKET_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'];

export default function Analytics({ results }: { results: ScreeningResult[] }) {
  const scoreData = bucketScores(results);
  const uniData = topUniversities(results);
  const skillData = topSkills(results);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-5">📊 Analytics</h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score distribution */}
        <div>
          <h3 className="text-sm font-medium text-gray-600 mb-3">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="range" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {scoreData.map((_, i) => (
                  <Cell key={i} fill={BUCKET_COLORS[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top universities */}
        <div>
          <h3 className="text-sm font-medium text-gray-600 mb-3">Top Universities</h3>
          {uniData.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={uniData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis type="number" tick={{ fontSize: 10 }} allowDecimals={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 9 }} width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top skills */}
        <div>
          <h3 className="text-sm font-medium text-gray-600 mb-3">Top Technical Skills</h3>
          {skillData.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={skillData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis type="number" tick={{ fontSize: 10 }} allowDecimals={false} />
                <YAxis dataKey="skill" type="category" tick={{ fontSize: 9 }} width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
