import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon, PlusCircle, Shield, Globe, Layers } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRoleBadge = (role) => {
    if (role === 'admin') {
      return <span className="px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-700 rounded-full border border-purple-200">Admin</span>;
    }
    if (role === 'survey_officer') {
      return <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full border border-blue-200">Survey Officer</span>;
    }
    return <span className="px-2 py-0.5 text-xs font-semibold bg-slate-100 text-slate-700 rounded-full border border-slate-200">Viewer</span>;
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      {/* Top micro-bar for Government of India styling */}
      <div className="bg-slate-900 text-slate-300 text-xs px-6 py-1 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-100">भारत सरकार | Government of India</span>
          <span className="text-slate-500">•</span>
          <span>Ministry of Rural Development</span>
          <span className="text-slate-500">•</span>
          <span className="text-amber-400 font-medium">Smart India Hackathon (SIH26012)</span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            GIS Engine Active (EPSG:4326)
          </span>
        </div>
      </div>

      {/* Main navigation header */}
      <div className="px-6 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-gov-700 to-gov-900 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
              <Layers className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-xl text-slate-900 tracking-tight">BHOOMI<span className="text-gov-600">-AI</span></span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">DILRMP</span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Drone-Based AI Parcel Mapping & Cadastral Verification</p>
            </div>
          </Link>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {user && (
            <Link
              to="/surveys/new"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gov-600 hover:bg-gov-700 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>New Survey</span>
            </Link>
          )}

          {user ? (
            <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
              <div className="text-right hidden sm:block">
                <div className="flex items-center gap-1.5 justify-end">
                  <span className="text-xs font-semibold text-slate-900">{user.name}</span>
                  {getRoleBadge(user.role)}
                </div>
                <p className="text-[11px] text-slate-500">{user.department}</p>
              </div>

              <button
                onClick={handleLogout}
                title="Sign Out"
                className="p-2 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gov-700 text-white text-xs font-semibold shadow-sm hover:bg-gov-800 transition-colors"
            >
              <UserIcon className="w-4 h-4" />
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
