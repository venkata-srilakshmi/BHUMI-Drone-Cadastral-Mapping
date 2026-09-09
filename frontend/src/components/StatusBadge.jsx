import React from 'react';

const statusConfig = {
  verified: { label: 'Verified', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  pending_review: { label: 'Pending Review', bg: 'bg-amber-50 text-amber-700 border-amber-200' },
  flagged_discrepancy: { label: 'Discrepancy Flagged', bg: 'bg-rose-50 text-rose-700 border-rose-200' },
  rejected: { label: 'Rejected', bg: 'bg-slate-100 text-slate-700 border-slate-300' },
  completed: { label: 'Completed', bg: 'bg-blue-50 text-blue-700 border-blue-200' },
  processing: { label: 'Processing', bg: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  draft: { label: 'Draft', bg: 'bg-slate-50 text-slate-600 border-slate-200' },
  failed: { label: 'Failed', bg: 'bg-red-50 text-red-700 border-red-200' },
  requires_review: { label: 'Requires Review', bg: 'bg-amber-50 text-amber-700 border-amber-200' },
  conforming: { label: 'Conforming', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
};

export default function StatusBadge({ status, size = 'sm' }) {
  const normStatus = (status || 'draft').toLowerCase();
  const config = statusConfig[normStatus] || {
    label: (status || '').replace('_', ' ').toUpperCase(),
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const sizeClass = size === 'xs' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border ${sizeClass} ${config.bg} tracking-wide uppercase font-mono`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-75"></span>
      {config.label}
    </span>
  );
}
