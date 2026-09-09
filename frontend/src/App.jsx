import React from 'react';
import { Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewSurvey from './pages/NewSurvey';
import ProcessingView from './pages/ProcessingView';
import SurveyMap from './pages/SurveyMap';
import ParcelTable from './pages/ParcelTable';
import ChangeDetection from './pages/ChangeDetection';
import Reports from './pages/Reports';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-gov-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function MainLayout({ children }) {
  const location = useLocation();
  // Extract surveyId from path if available, e.g. /surveys/1/map -> 1
  const match = location.pathname.match(/\/surveys\/(\d+)/);
  const surveyId = match ? parseInt(match[1], 10) : 1;

  // For the map view, we can collapse the sidebar or show it nicely
  const isMapView = location.pathname.includes('/map');

  return (
    <div className="min-h-screen flex flex-col bg-slate-100">
      <Navbar />
      <div className="flex-1 flex">
        {!isMapView && <Sidebar surveyId={surveyId} />}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys/new"
          element={
            <ProtectedRoute>
              <MainLayout>
                <NewSurvey />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys/:id/processing"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ProcessingView />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys/:id/map"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SurveyMap />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys/:id/parcels"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ParcelTable />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/change-detection"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ChangeDetection />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/surveys/:id/reports"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Reports />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
