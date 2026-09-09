import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileCheck,
  AlertCircle,
  Sparkles,
  ArrowRight,
  Layers,
  MapPin,
  Calendar,
  User,
  FileText
} from 'lucide-react';
import { createSurvey, uploadSurveyFiles, loadDemoSurvey } from '../services/api';

export default function NewSurvey() {
  const navigate = useNavigate();

  // Form state
  const [formData, setFormData] = useState({
    name: 'Ramnagar Village Cadastral Survey 2026',
    village: 'Ramnagar',
    mandal: 'Kothur',
    district: 'Rangareddy',
    state: 'Telangana',
    survey_date: '2026-03-08',
    survey_officer: 'K. Rajeshwar Rao, Dy. Inspector of Survey',
    description:
      'High-resolution drone orthomosaic survey for automated parcel extraction, cadastral discrepancy screening, and digital record update under DILRMP / SVAMITVA.'
  });

  const [orthoFile, setOrthoFile] = useState(null);
  const [cadastralFile, setCadastralFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCreateAndUpload = async (e) => {
    e.preventDefault();
    setError('');
    setUploading(true);

    try {
      // Validate cadastral file type before uploading
      if (cadastralFile) {
        const ext = cadastralFile.name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png', 'bmp', 'webp', 'gif'].includes(ext)) {
          setError(
            `Invalid cadastral dataset: '${cadastralFile.name}' is an image file. Cadastral maps must be vector datasets (GeoJSON, KML, Shapefile, GeoPackage).`
          );
          setUploading(false);
          return;
        }
      }

      // 1. Create survey
      const survey = await createSurvey(formData);

      // 2. Upload files if provided
      if (orthoFile || cadastralFile) {
        const uploadData = new FormData();
        if (orthoFile) uploadData.append('orthomosaic', orthoFile);
        if (cadastralFile) uploadData.append('cadastral', cadastralFile);
        await uploadSurveyFiles(survey.id, uploadData);
      }

      // Navigate to Processing View
      navigate(`/surveys/${survey.id}/processing`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to initialize survey.');
      setUploading(false);
    }
  };

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      const survey = await loadDemoSurvey();
      navigate(`/surveys/${survey.id}/map`);
    } catch (err) {
      console.error(err);
      setError('Failed to provision demo survey.');
    } finally {
      setLoadingDemo(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-gov-600 uppercase tracking-wider">
            Survey Management System
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Initiate New Drone Survey Project</h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure administrative metadata and ingest drone orthomosaic imagery with legacy cadastral vectors.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLoadDemo}
          disabled={loadingDemo}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all active:scale-95"
        >
          <Sparkles className="w-4 h-4" />
          <span>{loadingDemo ? 'Provisioning...' : 'Load Pre-Configured Demo'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleCreateAndUpload} className="space-y-6">
        {/* Step 1: Administrative Metadata */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-gov-600" />
              1. Administrative Survey Record
            </h3>
            <span className="text-[11px] text-slate-400">Step 1 of 2</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                Survey Project Name <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                Village / Revenue Settlement <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="village"
                required
                value={formData.village}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                Mandal / Tehsil <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="mandal"
                required
                value={formData.mandal}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                District <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="district"
                required
                value={formData.district}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                State / UT <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="state"
                required
                value={formData.state}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-700">
                Survey Flight Date <span className="text-rose-600">*</span>
              </label>
              <input
                type="date"
                name="survey_date"
                required
                value={formData.survey_date}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label className="block text-xs font-bold text-slate-700">
                Authorized Survey Officer <span className="text-rose-600">*</span>
              </label>
              <input
                type="text"
                name="survey_officer"
                required
                value={formData.survey_officer}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label className="block text-xs font-bold text-slate-700">Survey Description & Notes</label>
              <textarea
                rows={2}
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
              />
            </div>
          </div>
        </div>

        {/* Step 2: Ingest Imagery & Cadastral Vector */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-gov-600" />
              2. Data Ingestion (Drone Orthomosaic & Legacy Cadastral)
            </h3>
            <span className="text-[11px] text-slate-400">Step 2 of 2</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Orthomosaic Upload Box */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 hover:border-gov-500 transition-colors bg-slate-50/50 flex flex-col items-center justify-center text-center">
              <Layers className="w-8 h-8 text-gov-600 mb-2" />
              <p className="text-xs font-bold text-slate-800">Drone Orthomosaic Imagery</p>
              <p className="text-[11px] text-slate-500 mb-3">Supports GeoTIFF, PNG, JPG (OpenDroneMap output)</p>
              <input
                type="file"
                id="ortho-upload"
                accept=".tif,.tiff,.png,.jpg,.jpeg"
                onChange={(e) => setOrthoFile(e.target.files[0])}
                className="hidden"
              />
              <label
                htmlFor="ortho-upload"
                className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg cursor-pointer shadow-2xs transition-colors"
              >
                {orthoFile ? orthoFile.name : 'Choose Drone Orthomosaic'}
              </label>
              {orthoFile && (
                <span className="text-[10px] text-emerald-600 font-medium mt-2">
                  ✓ {(orthoFile.size / (1024 * 1024)).toFixed(2)} MB ready
                </span>
              )}
            </div>

            {/* Legacy Cadastral Upload Box */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 hover:border-gov-500 transition-colors bg-slate-50/50 flex flex-col items-center justify-center text-center">
              <FileCheck className="w-8 h-8 text-blue-600 mb-2" />
              <p className="text-xs font-bold text-slate-800">Existing Legacy Cadastral Map</p>
              <p className="text-[11px] text-slate-500 mb-3">Supports GeoJSON, KML, Shapefile / GeoPackage</p>
              <input
                type="file"
                id="cadastral-upload"
                accept=".geojson,.json,.kml"
                onChange={(e) => setCadastralFile(e.target.files[0])}
                className="hidden"
              />
              <label
                htmlFor="cadastral-upload"
                className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg cursor-pointer shadow-2xs transition-colors"
              >
                {cadastralFile ? cadastralFile.name : 'Choose Cadastral Vector'}
              </label>
              {cadastralFile && (
                <span className="text-[10px] text-emerald-600 font-medium mt-2">
                  ✓ {(cadastralFile.size / 1024).toFixed(1)} KB ready
                </span>
              )}
            </div>
          </div>

          <p className="text-[11px] text-slate-400 italic">
            * Note: If no files are uploaded, a realistic high-resolution synthetic drone orthomosaic will be
            generated automatically for prototype demonstration.
          </p>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={uploading}
            className="px-6 py-2.5 bg-gov-700 hover:bg-gov-800 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
          >
            {uploading ? 'Initializing Pipeline...' : 'Start AI & GIS Processing'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
