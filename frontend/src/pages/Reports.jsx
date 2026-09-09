import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Printer,
  ShieldCheck
} from 'lucide-react';
import {
  getSurvey,
  getSurveyParcels,
  getSurveyDiscrepancies,
  getPdfReportUrl,
  getExportUrl
} from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function Reports() {
  const { id } = useParams();
  const surveyId = parseInt(id, 10) || 1;

  const [survey, setSurvey] = useState(null);
  const [parcels, setParcels] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [s, p, d] = await Promise.all([
          getSurvey(surveyId),
          getSurveyParcels(surveyId),
          getSurveyDiscrepancies(surveyId)
        ]);
        setSurvey(s);
        setParcels(p);
        setDiscrepancies(d);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [surveyId]);

  const verifiedCount = parcels.filter((p) => p.status === 'verified').length;
  const pendingCount = parcels.filter((p) => p.status !== 'verified').length;
  const totalAcres = parcels.reduce((sum, p) => sum + (p.area_acres || 0), 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-gov-600 uppercase tracking-wider">
            Statutory Reporting & Geospatial Exporter
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">
            Cadastral Survey Audit Dossier
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {survey ? `${survey.name} • ${survey.village}, ${survey.mandal}, ${survey.district}` : 'Loading...'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={getPdfReportUrl(surveyId)}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 bg-gov-700 hover:bg-gov-800 text-white font-bold text-xs rounded-xl shadow-md transition-all"
          >
            <Printer className="w-4 h-4" />
            <span>Download Official PDF Dossier</span>
          </a>
        </div>
      </div>

      {/* Export Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* GeoJSON Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-900">Standard GeoJSON Format</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Standard OGC FeatureCollection containing high-precision polygons, area measurements,
              confidence tiers, and WGS84 coordinates for QGIS/ArcGIS ingestion.
            </p>
          </div>

          <a
            href={getExportUrl(surveyId, 'geojson')}
            download
            className="w-full py-2 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-800 text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Download GeoJSON</span>
          </a>
        </div>

        {/* CSV Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-900">Revenue Register (CSV)</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Tabular spreadsheet containing parcel identifiers, owner/land-use classification, metric areas,
              perimeters, verification status, and boundary displacement deltas.
            </p>
          </div>

          <a
            href={getExportUrl(surveyId, 'csv')}
            download
            className="w-full py-2 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-800 text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4 text-emerald-600" />
            <span>Download CSV Register</span>
          </a>
        </div>

        {/* KML Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <ExternalLink className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-900">Google Earth (KML)</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              OGC KML 2.2 vector file with color-coded styles for field GNSS handheld terminals, DGPS rovers,
              and 3D terrain visualization in Google Earth.
            </p>
          </div>

          <a
            href={getExportUrl(surveyId, 'kml')}
            download
            className="w-full py-2 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-800 text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4 text-amber-600" />
            <span>Download KML</span>
          </a>
        </div>
      </div>

      {/* Survey Dossier Preview Summary */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-gov-600" />
            Official Report Content & Statutory Certification
          </h3>
          <span className="text-[11px] font-mono text-slate-400">DILRMP-2026-SRV-{String(surveyId).padStart(4, '0')}</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block">Total Area Mapped</span>
            <span className="font-bold text-slate-900 text-base">{totalAcres.toFixed(2)} Acres</span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block">Total AI Parcels</span>
            <span className="font-bold text-gov-700 text-base">{parcels.length} Parcels</span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block">Verified by Officer</span>
            <span className="font-bold text-emerald-600 text-base">{verifiedCount} Approved</span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-medium block">Potential Discrepancies</span>
            <span className="font-bold text-rose-600 text-base">{discrepancies.length} Flagged</span>
          </div>
        </div>

        <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-200 text-xs text-blue-900 space-y-1">
          <p className="font-bold">National Cadastral Survey Endorsement Notice</p>
          <p className="leading-relaxed">
            The generated PDF audit dossier contains complete administrative survey details,
            cadastral feature distributions, discrepancy screening matrices, parcel boundary vertices,
            and designated endorsement signatures for the Survey Officer and Revenue Department (Tahsildar).
          </p>
        </div>
      </div>
    </div>
  );
}
