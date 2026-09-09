import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, Eye, EyeOff, CheckCircle2, ArrowRight, Layers } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('officer@bhoomi.gov.in');
  const [password, setPassword] = useState('Officer@2026');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      await login(normalizedEmail, password);
      navigate('/');
    } catch (err) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (Array.isArray(detail)) {
          setError(detail.map((d) => d.msg || JSON.stringify(d)).join(', '));
        } else {
          setError('Authentication failed. Please verify your credentials.');
        }
      } else if (!err.response) {
        setError(
          'Cannot reach BHOOMI-AI backend server. Please ensure the backend is running on http://localhost:8000.'
        );
      } else {
        setError('Authentication failed. Please verify your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (roleEmail, rolePwd) => {
    setEmail(roleEmail);
    setPassword(rolePwd);
    setError('');
  };

  return (
    <div className="min-h-[calc(100vh-85px)] bg-slate-100 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Government Emblem / Header Icon */}
        <div className="mx-auto w-14 h-14 rounded-2xl bg-gov-700 flex items-center justify-center text-white shadow-lg shadow-gov-700/30">
          <Layers className="w-8 h-8 text-amber-400" />
        </div>

        <h2 className="mt-5 text-center text-2xl font-bold tracking-tight text-slate-900">
          BHOOMI-AI Survey Portal
        </h2>
        <p className="mt-1 text-center text-xs font-medium text-slate-500">
          Ministry of Rural Development • Directorate of Survey & Land Records
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl border border-slate-200 sm:px-10">
          {error && (
            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <Shield className="w-4 h-4 text-rose-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleLogin}>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Official Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@bhoomi.gov.in"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
                />
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-gov-500 focus:border-gov-500 outline-hidden"
                />
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 text-gov-600 focus:ring-gov-500 border-slate-300 rounded-sm"
                />
                <label htmlFor="remember-me" className="ml-2 block text-xs text-slate-600">
                  Remember session
                </label>
              </div>
              <span className="text-xs text-slate-400">NIC Single Sign-On</span>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-xs font-bold text-white bg-gov-700 hover:bg-gov-800 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-gov-500 transition-colors"
              >
                {loading ? 'Authenticating...' : 'Sign In to Portal'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* Demo Roles Quick Selection Box */}
          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 text-center">
              Quick Demo Access Credentials
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setDemoCredentials('officer@bhoomi.gov.in', 'Officer@2026')}
                className="p-2 text-left rounded-lg border border-blue-200 bg-blue-50/50 hover:bg-blue-100/70 transition-colors group"
              >
                <p className="text-[11px] font-bold text-blue-900 group-hover:text-blue-950">Survey Officer</p>
                <p className="text-[10px] text-blue-700 font-mono">Officer@2026</p>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials('admin@bhoomi.gov.in', 'Admin@2026')}
                className="p-2 text-left rounded-lg border border-purple-200 bg-purple-50/50 hover:bg-purple-100/70 transition-colors group"
              >
                <p className="text-[11px] font-bold text-purple-900 group-hover:text-purple-950">Administrator</p>
                <p className="text-[10px] text-purple-700 font-mono">Admin@2026</p>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials('viewer@bhoomi.gov.in', 'Viewer@2026')}
                className="p-2 text-left rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors group"
              >
                <p className="text-[11px] font-bold text-slate-800">Public Viewer</p>
                <p className="text-[10px] text-slate-600 font-mono">Viewer@2026</p>
              </button>
            </div>
          </div>
        </div>

        <p className="mt-4 text-center text-xs text-slate-400">
          Smart India Hackathon SIH26012 • Digital Land Records Modernization
        </p>
      </div>
    </div>
  );
}
