import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MapPin,
  Table,
  FileCheck2,
  Layers,
  History,
  HelpCircle,
  FileSpreadsheet
} from 'lucide-react';

export default function Sidebar({ surveyId = 1 }) {
  const activeClass =
    'flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold bg-gov-50 text-gov-700 border-l-4 border-gov-600 transition-all';
  const inactiveClass =
    'flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all';

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-[calc(100vh-85px)] sticky top-[85px]">
      <div className="p-4 space-y-6 overflow-y-auto">
        {/* Main Section */}
        <div>
          <p className="px-3 text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            Operations & Analytics
          </p>
          <nav className="space-y-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Executive Dashboard</span>
            </NavLink>

            <NavLink
              to="/surveys"
              end
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <Layers className="w-4 h-4" />
              <span>Survey Registry</span>
            </NavLink>
          </nav>
        </div>

        {/* Survey Workspace Section */}
        <div>
          <div className="px-3 flex items-center justify-between mb-2">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Survey Workspace
            </p>
            <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
              SRV-{String(surveyId).padStart(4, '0')}
            </span>
          </div>

          <nav className="space-y-1">
            <NavLink
              to={`/surveys/${surveyId}/map`}
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <MapPin className="w-4 h-4" />
              <span>Interactive GIS Map</span>
            </NavLink>

            <NavLink
              to={`/surveys/${surveyId}/parcels`}
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <Table className="w-4 h-4" />
              <span>Parcel Inventory Table</span>
            </NavLink>

            <NavLink
              to="/change-detection"
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <History className="w-4 h-4" />
              <span>Change Detection</span>
            </NavLink>

            <NavLink
              to={`/surveys/${surveyId}/reports`}
              className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
            >
              <FileCheck2 className="w-4 h-4" />
              <span>Reports & Dossiers</span>
            </NavLink>
          </nav>
        </div>
      </div>

      {/* Footer Info Box */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50">
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-700">Decision-Support</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
          <p className="text-[10px] text-slate-500 leading-relaxed">
            AI boundaries are candidate screenings. Verification requires authorized Survey Officer approval.
          </p>
        </div>
      </div>
    </aside>
  );
}
