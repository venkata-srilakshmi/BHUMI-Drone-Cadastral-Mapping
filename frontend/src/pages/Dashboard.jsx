import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Layers,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  FileText,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  Sparkles,
  Building2
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { getDashboardAnalytics, getSurveys, loadDemoSurvey } from '../services/api';
import StatusBadge from '../components/StatusBadge';

const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#64748b', '#3b82f6'];

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [surveys, setSurveys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [analyticsData, surveysData] = await Promise.all([
        getDashboardAnalytics(),
        getSurveys()
      ]);
      setMetrics(analyticsData);
      setSurveys(surveysData);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      const s = await loadDemoSurvey();
      await fetchData();
      navigate(`/surveys/${s.id}/map`);
    } catch (err) {
      console.error('Failed to load demo', err);
    } finally {
      setLoadingDemo(false);
    }
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-gov-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs font-semibold text-slate-600">Loading Cadastral Analytics Engine...</p>
        </div>
      </div>
    );
  }

  const kpis = metrics?.kpis || {};
  const charts = metrics?.charts || {};

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Hero */}
      <div className="bg-gradient-to-r from-gov-900 via-gov-800 to-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-amber-400/20 text-amber-300 text-xs font-bold border border-amber-400/30">
              SVAMITVA • DILRMP National Mission
            </span>
            <span className="text-xs text-slate-300">SIH26012</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            BHOOMI-AI Executive Cadastral Dashboard
          </h1>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Automated boundary extraction, feature detection, and discrepancy screening for drone orthomosaics.
            Empowering survey officers with AI decision-support and statutory verification workflows.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={handleLoadDemo}
            disabled={loadingDemo}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-lg shadow-md transition-all transform active:scale-95"
          >
            <Sparkles className="w-4 h-4 text-slate-950" />
            <span>{loadingDemo ? 'Provisioning Demo...' : 'Load SIH Demo Survey'}</span>
          </button>

          <Link
            to="/surveys/new"
            className="flex items-center gap-2 px-4 py-2 bg-gov-600 hover:bg-gov-700 text-white font-bold text-xs rounded-lg shadow-md transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Survey</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Surveys</span>
            <Layers className="w-4 h-4 text-gov-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{kpis.total_surveys || 0}</p>
          <span className="text-[10px] text-slate-400">Orthomosaic projects</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">AI Parcels</span>
            <MapPin className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-700">{kpis.total_parcels || 0}</p>
          <span className="text-[10px] text-slate-400">{kpis.total_area_acres || 0} acres mapped</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Verified</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-700">{kpis.verified_parcels || 0}</p>
          <span className="text-[10px] text-emerald-600 font-medium">Officer approved</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Pending</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-amber-700">{kpis.pending_parcels || 0}</p>
          <span className="text-[10px] text-amber-600 font-medium">Awaiting review</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Discrepancies</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <p className="text-2xl font-bold text-rose-700">{kpis.total_discrepancies || 0}</p>
          <span className="text-[10px] text-rose-600 font-medium">Boundary shifts</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Cadastral Objects</span>
            <Building2 className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-purple-700">{kpis.total_features || 0}</p>
          <span className="text-[10px] text-slate-400">Structures & roads</span>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Verification Status Breakdown */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-gov-600" />
            Verification Status Distribution
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.verification_status || []}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={75}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {(charts.verification_status || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Land Use Classification */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gov-600" />
            Detected Land Use Classification
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.land_use || []}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#0259a0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cadastral Features Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-gov-600" />
            Cadastral Objects Detected
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.feature_distribution || []}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Surveys Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Survey Registry & Projects
            </h3>
            <p className="text-[11px] text-slate-500">Active orthomosaic surveys under officer adjudication</p>
          </div>

          <Link
            to="/surveys/new"
            className="text-xs font-semibold text-gov-600 hover:text-gov-800 flex items-center gap-1"
          >
            Create New Survey <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Survey Name</th>
                <th className="px-4 py-3">Location (Village / Mandal)</th>
                <th className="px-4 py-3">Survey Date</th>
                <th className="px-4 py-3">Survey Officer</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Parcels</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {surveys.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3 font-bold text-slate-900">
                    <Link to={`/surveys/${s.id}/map`} className="hover:text-gov-600 flex items-center gap-2">
                      <MapPin className="w-3.5 h-3.5 text-gov-600 shrink-0" />
                      <span>{s.name}</span>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {s.village}, {s.mandal}, {s.district}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-500">{s.survey_date}</td>
                  <td className="px-4 py-3 text-slate-700">{s.survey_officer}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="px-4 py-3 font-mono">
                    <span className="font-bold text-gov-700">{s.parcel_count || 0}</span>
                    <span className="text-slate-400"> ({s.verified_count || 0} verified)</span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <Link
                      to={`/surveys/${s.id}/map`}
                      className="px-2.5 py-1 rounded bg-gov-50 text-gov-700 hover:bg-gov-100 font-semibold text-[11px] transition-colors"
                    >
                      GIS Map
                    </Link>
                    <Link
                      to={`/surveys/${s.id}/reports`}
                      className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-semibold text-[11px] transition-colors"
                    >
                      Dossier
                    </Link>
                  </td>
                </tr>
              ))}

              {surveys.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400">
                    No surveys found. Click "Load SIH Demo Survey" or "New Survey" to begin.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
