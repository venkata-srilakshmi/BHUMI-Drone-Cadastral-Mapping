import React, { useState, useEffect } from 'react';
import {
  History,
  Layers,
  ArrowRight,
  Building2,
  AlertTriangle,
  TrendingUp,
  MapPin,
  CheckCircle2,
  Play
} from 'lucide-react';
import { MapContainer, TileLayer, Polygon, Polyline, Popup } from 'react-leaflet';
import { getSurveys, executeChangeDetection, getChangeDetectionRuns } from '../services/api';

export default function ChangeDetection() {
  const [surveys, setSurveys] = useState([]);
  const [surveyAId, setSurveyAId] = useState('');
  const [surveyBId, setSurveyBId] = useState('');
  const [running, setRunning] = useState(false);
  const [changeResult, setChangeResult] = useState(null);
  const [pastRuns, setPastRuns] = useState([]);

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [sList, runs] = await Promise.all([
          getSurveys(),
          getChangeDetectionRuns()
        ]);
        setSurveys(sList);
        if (sList.length > 0) {
          setSurveyAId(sList[0].id);
          setSurveyBId(sList[sList.length - 1].id);
        }
        if (runs.length > 0) {
          setPastRuns(runs);
          setChangeResult(runs[0]);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchInit();
  }, []);

  const handleRunChangeDetection = async (e) => {
    e.preventDefault();
    if (!surveyAId || !surveyBId) return;
    setRunning(true);
    try {
      const res = await executeChangeDetection(parseInt(surveyAId, 10), parseInt(surveyBId, 10));
      setChangeResult(res);
      const runs = await getChangeDetectionRuns();
      setPastRuns(runs);
    } catch (err) {
      console.error(err);
      alert('Change detection failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunning(false);
    }
  };

  const mapCenter = [17.153, 78.294];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-gov-600 uppercase tracking-wider">
            Temporal GIS Analysis
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">
            Multi-Temporal Cadastral Change Detection
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Compare baseline revenue records or past drone surveys against latest orthomosaic captures to
            isolate newly constructed buildings, removed structures, and parcel boundary shifts.
          </p>
        </div>
      </div>

      {/* Comparison Selector Form */}
      <form
        onSubmit={handleRunChangeDetection}
        className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col sm:flex-row items-end gap-4"
      >
        <div className="flex-1 space-y-1">
          <label className="block text-xs font-bold text-slate-700">Baseline Survey (T1)</label>
          <select
            value={surveyAId}
            onChange={(e) => setSurveyAId(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-gov-500 outline-hidden font-medium"
          >
            {surveys.map((s) => (
              <option key={`a-${s.id}`} value={s.id}>
                {s.name} ({s.survey_date})
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 space-y-1">
          <label className="block text-xs font-bold text-slate-700">Latest Drone Survey (T2)</label>
          <select
            value={surveyBId}
            onChange={(e) => setSurveyBId(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-gov-500 outline-hidden font-medium"
          >
            {surveys.map((s) => (
              <option key={`b-${s.id}`} value={s.id}>
                {s.name} ({s.survey_date})
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={running}
          className="px-6 py-2.5 bg-gov-600 hover:bg-gov-700 text-white font-bold text-xs rounded-lg shadow-sm transition-all flex items-center gap-2 shrink-0"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>{running ? 'Analyzing Deltas...' : 'Run Change Detection'}</span>
        </button>
      </form>

      {/* Results Section */}
      {changeResult && (
        <div className="space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <span className="text-[11px] font-bold text-slate-500 uppercase">New Buildings</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                +{changeResult.new_buildings_count}
              </p>
              <span className="text-[10px] text-slate-400">Newly constructed</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <span className="text-[11px] font-bold text-slate-500 uppercase">Removed Structures</span>
              <p className="text-2xl font-bold text-rose-600 mt-1">
                -{changeResult.removed_structures_count}
              </p>
              <span className="text-[10px] text-slate-400">Demolished or cleared</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <span className="text-[11px] font-bold text-slate-500 uppercase">Boundary Changes</span>
              <p className="text-2xl font-bold text-amber-600 mt-1">
                {changeResult.boundary_changes_count}
              </p>
              <span className="text-[10px] text-slate-400">Realignment detected</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <span className="text-[11px] font-bold text-slate-500 uppercase">Land-Use Shifts</span>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {changeResult.landuse_changes_count}
              </p>
              <span className="text-[10px] text-slate-400">Classification altered</span>
            </div>
          </div>

          {/* Interactive Change Map + Summary Drawer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Map */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden h-[450px] relative">
              <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs font-bold text-slate-800 z-10 relative">
                <span>Spatial Change Map (T1 vs T2)</span>
                <span className="text-[11px] text-slate-500">Green = New Structure • Red = Shifted Boundary</span>
              </div>

              <MapContainer center={mapCenter} zoom={16} className="w-full h-[400px]">
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  attribution="&copy; Esri &mdash; World Imagery"
                  maxZoom={19}
                />

                {/* Sample Change Overlay polygons */}
                <Polygon
                  positions={[
                    [17.1548, 78.2915],
                    [17.1548, 78.2921],
                    [17.1544, 78.2921],
                    [17.1544, 78.2915],
                  ]}
                  pathOptions={{
                    color: '#10b981',
                    fillColor: '#34d399',
                    fillOpacity: 0.7,
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div className="p-1 text-xs">
                      <p className="font-bold text-emerald-800">New Construction (late 2025)</p>
                      <p className="text-[10px] text-slate-500">Agro-shed detected on parcel P-101</p>
                    </div>
                  </Popup>
                </Polygon>

                <Polyline
                  positions={[
                    [17.1536, 78.2933],
                    [17.1536, 78.2935],
                  ]}
                  pathOptions={{
                    color: '#f43f5e',
                    weight: 5,
                  }}
                />
              </MapContainer>
            </div>

            {/* Change Details Checklist */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
                <Layers className="w-4 h-4 text-gov-600" />
                Change Inventory Summary
              </h3>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block mb-1">New Structures:</span>
                  <ul className="list-disc list-inside text-slate-600 space-y-1">
                    {changeResult.change_summary?.new_buildings?.map((b, i) => (
                      <li key={i}>{b}</li>
                    )) || <li>No new structures detected</li>}
                  </ul>
                </div>

                <div>
                  <span className="font-bold text-slate-700 block mb-1">Removed Structures:</span>
                  <ul className="list-disc list-inside text-slate-600 space-y-1">
                    {changeResult.change_summary?.removed_structures?.map((r, i) => (
                      <li key={i}>{r}</li>
                    )) || <li>No removed structures</li>}
                  </ul>
                </div>

                <div>
                  <span className="font-bold text-slate-700 block mb-1">Boundary Realignment:</span>
                  <ul className="list-disc list-inside text-slate-600 space-y-1">
                    {changeResult.change_summary?.boundary_shifts?.map((s, i) => (
                      <li key={i}>{s}</li>
                    )) || <li>Boundaries consistent</li>}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
