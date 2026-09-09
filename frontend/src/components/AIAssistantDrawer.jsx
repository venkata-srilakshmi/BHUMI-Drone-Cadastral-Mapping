import React, { useState } from 'react';
import { Sparkles, Search, CheckCircle2, ChevronRight, X, AlertCircle } from 'lucide-react';
import { queryAIAssistant } from '../services/api';

const SUGGESTED_QUERIES = [
  "Show buildings inside agricultural parcels",
  "Show parcels with boundary discrepancies",
  "Show low-confidence parcels",
  "How many parcels require verification?",
  "Show parcels near roads"
];

export default function AIAssistantDrawer({ surveyId, onHighlightParcels, onClose }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (queryText) => {
    const q = queryText || query;
    if (!q || !q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await queryAIAssistant(surveyId, q);
      setResult(data);
      if (onHighlightParcels && data.matched_parcel_ids) {
        onHighlightParcels(data.matched_parcel_ids);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Query execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-3.5 bg-gradient-to-r from-gov-800 to-gov-900 text-white flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-amber-400/20 text-amber-300">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-xs">AI Geospatial Assistant</h4>
            <p className="text-[10px] text-slate-300">Natural-Language Cadastral Query Engine</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-sm">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Query input */}
      <div className="p-3 border-b border-slate-200 bg-slate-50">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch(query);
          }}
          className="relative"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Show buildings inside agricultural parcels"
            className="w-full pl-8 pr-16 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-1.5 top-1.5 px-2.5 py-1 bg-gov-600 hover:bg-gov-700 text-white text-[11px] font-semibold rounded-md transition-colors"
          >
            {loading ? '...' : 'Ask'}
          </button>
        </form>

        {/* Suggested Prompts */}
        <div className="mt-2.5 space-y-1">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Suggested Queries:</p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUERIES.map((sq, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(sq);
                  handleSearch(sq);
                }}
                className="text-[11px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-gov-700 hover:border-gov-300 hover:bg-gov-50 transition-colors text-left"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Display */}
      <div className="p-3 overflow-y-auto flex-1 space-y-3">
        {error && (
          <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="p-3 bg-gov-50 border border-gov-200 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-gov-900 uppercase">Interpretation</span>
              <span className="text-[10px] font-semibold px-2 py-0.5 bg-gov-100 text-gov-800 rounded-full">
                {result.count} Match(es)
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {result.summary_message}
            </p>

            {result.matched_parcel_ids.length > 0 && (
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1">
                  Highlighted on Map:
                </p>
                <div className="flex flex-wrap gap-1">
                  {result.matched_parcel_ids.map((pid) => (
                    <span
                      key={pid}
                      className="px-2 py-0.5 bg-white border border-gov-300 text-gov-800 font-mono text-xs rounded-md shadow-2xs font-semibold"
                    >
                      {pid}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !loading && (
          <div className="text-center py-6 text-slate-400 space-y-1">
            <Search className="w-8 h-8 mx-auto stroke-1 opacity-50" />
            <p className="text-xs font-medium">Ask natural-language questions about this survey.</p>
            <p className="text-[11px] text-slate-400">All queries execute against verified spatial indexes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
