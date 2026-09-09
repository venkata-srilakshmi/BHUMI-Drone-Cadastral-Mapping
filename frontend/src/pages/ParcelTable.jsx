import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Download,
  MapPin,
  FileSpreadsheet,
  Layers,
  ArrowUpDown,
  ExternalLink,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { getSurveyParcels, getSurvey, getExportUrl } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import ConfidenceBadge from '../components/ConfidenceBadge';

export default function ParcelTable() {
  const { id } = useParams();
  const surveyId = parseInt(id, 10) || 1;
  const navigate = useNavigate();

  const [survey, setSurvey] = useState(null);
  const [parcels, setParcels] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('parcel_id');
  const [sortDirection, setSortDirection] = useState('asc'); // 'asc' | 'desc'
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [sData, pData] = await Promise.all([
          getSurvey(surveyId),
          getSurveyParcels(surveyId)
        ]);
        setSurvey(sData);
        setParcels(pData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [surveyId]);

  // Sorting
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Filtered & sorted parcels
  const filtered = parcels
    .filter((p) => {
      const matchesSearch =
        p.parcel_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.land_use.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === 'all' ? true : p.status.toLowerCase() === statusFilter.toLowerCase();
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-gov-600 uppercase tracking-wider">
            Land Records Register
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">
            Parcel Inventory Table & Audit Records
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {survey ? `${survey.name} • ${survey.village}, ${survey.mandal}` : 'Loading survey...'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={getExportUrl(surveyId, 'csv')}
            download
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Export CSV</span>
          </a>

          <a
            href={getExportUrl(surveyId, 'geojson')}
            download
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gov-50 border border-gov-200 hover:bg-gov-100 text-gov-700 text-xs font-semibold shadow-2xs transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export GeoJSON</span>
          </a>

          <Link
            to={`/surveys/${surveyId}/map`}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gov-600 hover:bg-gov-700 text-white text-xs font-bold shadow-sm transition-colors"
          >
            <MapPin className="w-4 h-4" />
            <span>Interactive Map</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search parcel ID, land use classification..."
            className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Status:
          </span>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-gov-500 outline-hidden font-medium text-slate-700"
          >
            <option value="all">All Parcels</option>
            <option value="verified">Verified Only</option>
            <option value="pending_review">Pending Review</option>
            <option value="flagged_discrepancy">Discrepancy Flagged</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th
                  onClick={() => handleSort('parcel_id')}
                  className="px-4 py-3 cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Parcel ID</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('area_acres')}
                  className="px-4 py-3 cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Area (Acres)</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="px-4 py-3">Area (Sq.m)</th>
                <th className="px-4 py-3">Perimeter (m)</th>
                <th
                  onClick={() => handleSort('confidence')}
                  className="px-4 py-3 cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>AI Confidence</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="px-4 py-3">Land Use</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Boundary Shift</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
              {paginated.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3 font-bold text-slate-900 flex items-center gap-1.5 font-mono">
                    <MapPin className="w-3.5 h-3.5 text-gov-600 shrink-0" />
                    <span>{p.parcel_id}</span>
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold text-gov-800">
                    {p.area_acres.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-600">{p.area.toLocaleString()}</td>
                  <td className="px-4 py-3 font-mono text-slate-600">{p.perimeter.toFixed(1)}</td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge score={p.confidence} />
                  </td>
                  <td className="px-4 py-3">{p.land_use}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {p.discrepancy ? (
                      <span className="text-rose-600 font-bold">
                        {p.discrepancy.difference_distance}m
                      </span>
                    ) : (
                      <span className="text-emerald-600">Conforming</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/surveys/${surveyId}/map`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-gov-50 text-gov-700 hover:bg-gov-100 font-semibold text-[11px] transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Inspect</span>
                    </Link>
                  </td>
                </tr>
              ))}

              {paginated.length === 0 && (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-400">
                    No parcels found matching filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, filtered.length)} of {filtered.length} parcels
          </span>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-slate-800 px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
