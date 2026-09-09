import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  Loader2,
  MapPin,
  FileText,
  AlertCircle,
  Terminal,
  Layers,
  ArrowRight
} from 'lucide-react';
import { getSurveyStatus, startSurveyProcessing, getSurvey } from '../services/api';

const PIPELINE_STAGES = [
  'File Validation',
  'Image Preprocessing',
  'Orthomosaic Validation',
  'AI Parcel Segmentation',
  'Cadastral Feature Detection',
  'Boundary Extraction',
  'Polygon Generation',
  'GIS Validation',
  'Change & Discrepancy Screening',
  'Processing Completed'
];

export default function ProcessingView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [survey, setSurvey] = useState(null);
  const [status, setStatus] = useState('processing');
  const [progress, setProgress] = useState(10);
  const [currentStep, setCurrentStep] = useState('File Validation');
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const hasTriggeredRef = React.useRef(false);

  useEffect(() => {
    let interval = null;

    const init = async () => {
      try {
        const s = await getSurvey(id);
        setSurvey(s);
        if (!hasTriggeredRef.current && (s.status === 'draft' || s.status === 'uploaded')) {
          hasTriggeredRef.current = true;
          await startSurveyProcessing(id);
        }
      } catch (err) {
        console.error(err);
        setError('Failed to contact processing pipeline service.');
      }
    };

    init();

    // Poll status
    interval = setInterval(async () => {
      try {
        const st = await getSurveyStatus(id);
        setStatus(st.status);
        setProgress(st.progress);
        setCurrentStep(st.current_step);
        setLogs(st.logs || []);

        if (st.status === 'completed' || st.status === 'failed') {
          clearInterval(interval);
        }
      } catch (e) {
        console.error('Polling error', e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [id]);

  const isStepCompleted = (stepName, index) => {
    const currentIndex = PIPELINE_STAGES.indexOf(currentStep);
    if (status === 'completed') return true;
    return index < currentIndex;
  };

  const isStepActive = (stepName) => {
    if (status === 'completed') return false;
    return currentStep.toLowerCase().includes(stepName.toLowerCase()) || currentStep === stepName;
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-gov-600 uppercase tracking-wider">
            Automated Processing Pipeline
          </span>
          <h1 className="text-xl font-bold text-slate-900 mt-1">
            {survey ? survey.name : `Survey Project SRV-${String(id).padStart(4, '0')}`}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {survey ? `${survey.village}, ${survey.mandal}, ${survey.district}` : 'Initializing pipeline...'}
          </p>
        </div>

        {status === 'completed' && (
          <Link
            to={`/surveys/${id}/map`}
            className="flex items-center gap-2 px-5 py-2.5 bg-gov-600 hover:bg-gov-700 text-white font-bold text-xs rounded-xl shadow-md transition-all animate-bounce"
          >
            <span>Open Interactive GIS Map</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {/* Progress Bar & Status */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs font-bold text-slate-800">
          <div className="flex items-center gap-2">
            {status === 'completed' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <Loader2 className="w-4 h-4 text-gov-600 animate-spin" />
            )}
            <span>Current Operation: {currentStep}</span>
          </div>
          <span className="font-mono text-gov-700 text-sm">{progress}%</span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              status === 'completed'
                ? 'bg-emerald-500'
                : 'bg-gradient-to-r from-gov-600 to-gov-400'
            }`}
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* 10-Stage Pipeline Checklist */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="font-bold text-xs uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-gov-600" />
          Processing Pipeline Stages (10 Steps)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {PIPELINE_STAGES.map((stage, idx) => {
            const completed = isStepCompleted(stage, idx);
            const active = isStepActive(stage);

            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border flex items-center justify-between text-xs transition-all ${
                  completed
                    ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900'
                    : active
                    ? 'bg-blue-50 border-blue-300 text-blue-950 font-bold shadow-xs'
                    : 'bg-slate-50/50 border-slate-200 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full flex items-center justify-center font-mono text-[10px] bg-white border border-current">
                    {idx + 1}
                  </span>
                  <span>{stage}</span>
                </div>

                {completed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : active ? (
                  <Loader2 className="w-4 h-4 text-gov-600 animate-spin" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-slate-300" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Failure Alert Banner */}
      {status === 'failed' && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5 text-rose-800 space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm text-rose-900">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <span>Pipeline Execution Halted</span>
          </div>
          <p className="text-xs leading-relaxed text-rose-700">
            {logs.find((l) => l.includes('[ERROR]'))?.replace(/.*\[ERROR\]\s*/, '') ||
              'Processing failed during geospatial or AI execution. Please verify uploaded datasets.'}
          </p>
        </div>
      )}

      {/* Real-time System Logs Terminal */}
      <div className="bg-slate-950 text-slate-200 rounded-2xl border border-slate-800 p-5 shadow-lg space-y-2">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-amber-400" />
            <span>AI Inference & GIS Engine Pipeline Logs</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono">
            {status === 'processing' ? 'STREAMING' : status.toUpperCase()}
          </span>
        </div>

        <div className="h-48 overflow-y-auto font-mono text-[11px] space-y-1 text-slate-300 pr-2">
          {Array.from(new Set(logs)).map((log, index) => {
            const isError = log.includes('[ERROR]');
            return (
              <div
                key={index}
                className={`leading-relaxed ${isError ? 'text-rose-400 font-semibold' : ''}`}
              >
                <span className="text-slate-500 mr-1">&gt;</span>
                {log}
              </div>
            );
          })}
          {logs.length === 0 && (
            <p className="text-slate-600 italic">Initializing execution worker thread...</p>
          )}
        </div>
      </div>
    </div>
  );
}
