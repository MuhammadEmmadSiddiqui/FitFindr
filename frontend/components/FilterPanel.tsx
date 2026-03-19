'use client';
import { useState, useEffect } from 'react';
import { ScreeningResult } from '@/types';

interface Props {
  results: ScreeningResult[];
  onFilter: (filtered: ScreeningResult[]) => void;
}

export default function FilterPanel({ results, onFilter }: Props) {
  const [minScore, setMinScore] = useState(0);
  const [selectedUnis, setSelectedUnis] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  const allUnis = Array.from(
    new Set(results.map((r) => r.university_name).filter((u) => u && u !== 'N/A'))
  ).sort();

  const allSkills = Array.from(
    new Set(results.flatMap((r) => r.technical_skills ?? []))
  ).sort();

  useEffect(() => {
    const filtered = results.filter((r) => {
      if (r.similarity_score < minScore) return false;
      if (selectedUnis.length > 0 && !selectedUnis.includes(r.university_name)) return false;
      if (
        selectedSkills.length > 0 &&
        !selectedSkills.some((s) => (r.technical_skills ?? []).includes(s))
      )
        return false;
      return true;
    });
    onFilter(filtered);
  }, [minScore, selectedUnis, selectedSkills, results]); // eslint-disable-line react-hooks/exhaustive-deps

  function toggleUni(uni: string) {
    setSelectedUnis((prev) =>
      prev.includes(uni) ? prev.filter((u) => u !== uni) : [...prev, uni]
    );
  }

  function toggleSkill(skill: string) {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  }

  function reset() {
    setMinScore(0);
    setSelectedUnis([]);
    setSelectedSkills([]);
  }

  const activeFilters = (minScore > 0 ? 1 : 0) + selectedUnis.length + selectedSkills.length;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">
          Filters{' '}
          {activeFilters > 0 && (
            <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
              {activeFilters}
            </span>
          )}
        </h2>
        {activeFilters > 0 && (
          <button onClick={reset} className="text-xs text-gray-500 hover:text-gray-700 underline">
            Reset
          </button>
        )}
      </div>

      {/* Min score */}
      <div className="mb-5">
        <label className="block text-xs font-medium text-gray-600 mb-2">
          Min Match Score — <span className="text-indigo-600 font-semibold">{Math.round(minScore * 100)}%</span>
        </label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={minScore}
          onChange={(e) => setMinScore(parseFloat(e.target.value))}
          className="w-full accent-indigo-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>0%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Universities */}
      {allUnis.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium text-gray-600 mb-2">University</p>
          <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
            {allUnis.map((uni) => (
              <button
                key={uni}
                onClick={() => toggleUni(uni)}
                className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                  selectedUnis.includes(uni)
                    ? 'bg-indigo-100 border-indigo-400 text-indigo-700'
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-400'
                }`}
              >
                {uni}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Skills */}
      {allSkills.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-600 mb-2">Required Skill (any)</p>
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pr-1">
            {allSkills.map((skill) => (
              <button
                key={skill}
                onClick={() => toggleSkill(skill)}
                className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                  selectedSkills.includes(skill)
                    ? 'bg-sky-100 border-sky-400 text-sky-700'
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-400'
                }`}
              >
                {skill}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
