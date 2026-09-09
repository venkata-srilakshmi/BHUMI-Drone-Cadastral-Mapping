import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, X } from 'lucide-react';

export default function BoundaryEditorModal({
  isOpen,
  onClose,
  onSave,
  parcel,
  originalArea,
  adjustedArea,
  saving
}) {
  const [reason, setReason] = useState('Boundary adjusted based on physical ground survey pillar verification');
  const [error, setError] = useState('');

  if (!isOpen || !parcel) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reason || reason.trim().length < 5) {
      setError('Please provide a valid official justification (min 5 characters).');
      return;
    }
    setError('');
    onSave(reason);
  };

  const diffAcres = Math.abs((adjustedArea || parcel.area_acres) - (originalArea || parcel.area_acres));
  const diffPct = ((diffAcres / (originalArea || parcel.area_acres || 1)) * 100).toFixed(2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gov-600 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-sm">Commit Boundary Adjustment</h3>
              <p className="text-xs text-slate-400">Parcel: {parcel.parcel_id} • Statutory Audit Trail</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3.5 bg-amber-50 rounded-lg border border-amber-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-900 space-y-1">
              <p className="font-semibold">Human-in-the-Loop Audit Requirement</p>
              <p>
                The original AI-extracted polygon will be preserved immutably. Your modified geometry,
                timestamp, and official justification will be logged in the permanent survey record.
              </p>
            </div>
          </div>

          {/* Area Comparison */}
          <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <div>
              <p className="text-slate-500 font-medium">AI-Detected Area</p>
              <p className="font-bold text-slate-800 text-sm">{(originalArea || parcel.area_acres).toFixed(3)} acres</p>
            </div>
            <div>
              <p className="text-slate-500 font-medium">Adjusted Area</p>
              <p className="font-bold text-gov-700 text-sm">{(adjustedArea || parcel.area_acres).toFixed(3)} acres</p>
              <span className="text-[10px] text-slate-500">Variation: {diffPct}%</span>
            </div>
          </div>

          {/* Reason Input */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700">
              Official Justification for Modification <span className="text-rose-600">*</span>
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g., Adjusted eastern boundary to align with physical stone bund verified on-site by DGPS rover."
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              required
            />
            {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-xs font-semibold text-white bg-gov-600 hover:bg-gov-700 rounded-lg shadow-sm transition-colors flex items-center gap-2"
            >
              {saving ? 'Saving Adjustment...' : 'Commit & Update Geometry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
