import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  MapContainer,
  TileLayer,
  Polygon,
  Polyline,
  Marker,
  Popup,
  useMap,
  useMapEvents
} from 'react-leaflet';
import L from 'leaflet';
import {
  Layers,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Edit3,
  Sparkles,
  Search,
  Filter,
  Download,
  FileText,
  X,
  Eye,
  Maximize2
} from 'lucide-react';
import {
  getSurvey,
  getSurveyParcels,
  getSurveyFeatures,
  getSurveyDiscrepancies,
  updateParcelGeometry,
  verifyParcel,
  rejectParcel,
  getPdfReportUrl,
  getExportUrl
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import ConfidenceBadge from '../components/ConfidenceBadge';
import BoundaryEditorModal from '../components/BoundaryEditorModal';
import AIAssistantDrawer from '../components/AIAssistantDrawer';

// Custom draggable marker icon for polygon vertex editing
const createVertexIcon = () =>
  L.divIcon({
    className: 'editing-vertex-marker',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

// Component to handle mouse coordinates display
function CoordinateTracker({ onCoordinatesChange }) {
  useMapEvents({
    mousemove(e) {
      if (onCoordinatesChange) {
        onCoordinatesChange({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    },
  });
  return null;
}

// Component to handle zooming to a parcel
function MapFlyTo({ targetCoords }) {
  const map = useMap();
  useEffect(() => {
    if (targetCoords && targetCoords.length > 0) {
      const bounds = L.latLngBounds(targetCoords);
      map.flyToBounds(bounds, { padding: [50, 50], maxZoom: 18, duration: 1 });
    }
  }, [targetCoords, map]);
  return null;
}

export default function SurveyMap() {
  const { id } = useParams();
  const surveyId = parseInt(id, 10) || 1;

  // Data states
  const [survey, setSurvey] = useState(null);
  const [parcels, setParcels] = useState([]);
  const [features, setFeatures] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [loading, setLoading] = useState(true);

  // Map layer toggles
  const [baseMap, setBaseMap] = useState('satellite'); // 'satellite' | 'streets'
  const [showParcels, setShowParcels] = useState(true);
  const [showCadastral, setShowCadastral] = useState(true);
  const [showBuildings, setShowBuildings] = useState(true);
  const [showRoads, setShowRoads] = useState(true);
  const [showWater, setShowWater] = useState(true);
  const [showDiscrepancies, setShowDiscrepancies] = useState(true);

  // Filters & AI Assistant
  const [statusFilter, setStatusFilter] = useState('all');
  const [highlightedParcelIds, setHighlightedParcelIds] = useState([]);
  const [showAIDrawer, setShowAIDrawer] = useState(false);
  const [mouseCoords, setMouseCoords] = useState({ lat: 17.152, lng: 78.293 });

  // Human-in-the-loop vertex editing states
  const [isEditing, setIsEditing] = useState(false);
  const [editableCoords, setEditableCoords] = useState([]); // [[lat, lng], ...]
  const [showCommitModal, setShowCommitModal] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [flyTarget, setFlyTarget] = useState(null);

  // Load survey data
  const loadData = async () => {
    try {
      setLoading(true);
      const [sData, pData, fData, dData] = await Promise.all([
        getSurvey(surveyId),
        getSurveyParcels(surveyId),
        getSurveyFeatures(surveyId),
        getSurveyDiscrepancies(surveyId),
      ]);
      setSurvey(sData);
      setParcels(pData);
      setFeatures(fData);
      setDiscrepancies(dData);
      if (pData.length > 0 && !selectedParcel) {
        setSelectedParcel(pData[0]);
      }
    } catch (err) {
      console.error('Failed to load map data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [surveyId]);

  // Handle parcel selection
  const handleSelectParcel = (parcel) => {
    if (isEditing) return; // Prevent selection changes during edit
    setSelectedParcel(parcel);
    // Extract coords for fly-to
    const geom = parcel.geometry;
    if (geom && geom.coordinates) {
      const latlngs = geom.coordinates[0].map(([lng, lat]) => [lat, lng]);
      setFlyTarget(latlngs);
    }
  };

  // Activate Human-in-the-loop editing mode
  const startEditing = () => {
    if (!selectedParcel) return;
    const geom = selectedParcel.geometry;
    if (geom && geom.coordinates) {
      // Leaflet uses [lat, lng]
      const latlngs = geom.coordinates[0].map(([lng, lat]) => [lat, lng]);
      // Remove duplicate closing point for easier vertex editing
      if (
        latlngs.length > 1 &&
        latlngs[0][0] === latlngs[latlngs.length - 1][0] &&
        latlngs[0][1] === latlngs[latlngs.length - 1][1]
      ) {
        latlngs.pop();
      }
      setEditableCoords(latlngs);
      setIsEditing(true);
    }
  };

  // Handle vertex drag
  const handleVertexDrag = (index, e) => {
    const newLatLng = e.target.getLatLng();
    const updated = [...editableCoords];
    updated[index] = [newLatLng.lat, newLatLng.lng];
    setEditableCoords(updated);
  };

  // Cancel editing
  const cancelEditing = () => {
    setIsEditing(false);
    setEditableCoords([]);
  };

  // Commit edited geometry
  const handleSaveGeometry = async (reason) => {
    if (!selectedParcel || editableCoords.length < 3) return;
    setSavingEdit(true);
    try {
      // Re-close the polygon loop for GeoJSON [lng, lat]
      const geojsonCoords = editableCoords.map(([lat, lng]) => [
        parseFloat(lng.toFixed(6)),
        parseFloat(lat.toFixed(6)),
      ]);
      geojsonCoords.push(geojsonCoords[0]); // close loop

      const updatedGeometry = {
        type: 'Polygon',
        coordinates: [geojsonCoords],
      };

      const updatedParcel = await updateParcelGeometry(selectedParcel.id, updatedGeometry, reason);
      // Refresh parcels
      await loadData();
      setSelectedParcel(updatedParcel);
      setIsEditing(false);
      setShowCommitModal(false);
    } catch (err) {
      console.error('Failed to update geometry', err);
      alert('Error updating geometry: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingEdit(false);
    }
  };

  // Handle Verify Parcel
  const handleVerify = async () => {
    if (!selectedParcel) return;
    try {
      await verifyParcel(selectedParcel.id, 'Verified on-site by Survey Officer');
      await loadData();
    } catch (err) {
      alert('Error verifying parcel: ' + err.message);
    }
  };

  // Handle Reject Parcel
  const handleReject = async () => {
    if (!selectedParcel) return;
    const reason = prompt('Please enter reason for rejection:', 'Boundary overlaps unapproved expansion');
    if (!reason) return;
    try {
      await rejectParcel(selectedParcel.id, reason);
      await loadData();
    } catch (err) {
      alert('Error rejecting parcel: ' + err.message);
    }
  };

  // Filter parcels
  const filteredParcels = parcels.filter((p) => {
    if (statusFilter === 'all') return true;
    if (statusFilter === 'verified') return p.status === 'verified';
    if (statusFilter === 'pending') return p.status === 'pending_review';
    if (statusFilter === 'discrepancy') return p.status === 'flagged_discrepancy';
    if (statusFilter === 'low_confidence') return p.confidence < 0.85;
    return true;
  });

  // Calculate center of survey for map initialization
  const defaultCenter = [17.1527, 78.2938];

  return (
    <div className="h-[calc(100vh-85px)] flex flex-col overflow-hidden bg-slate-100">
      {/* Top Map Action Bar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between z-30 shrink-0 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-800">
              {survey ? survey.name : 'Loading Survey...'}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-bold">
              EPSG:4326 WGS84
            </span>
          </div>

          <div className="h-4 w-px bg-slate-200 hidden sm:block"></div>

          {/* Quick Filters */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs">
            <span className="text-slate-500 font-medium">Filter:</span>
            {['all', 'verified', 'pending', 'discrepancy', 'low_confidence'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2 py-0.5 rounded-md text-[11px] font-semibold transition-colors ${
                  statusFilter === st
                    ? 'bg-gov-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {st.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-2">
          {/* AI Assistant toggle */}
          <button
            onClick={() => setShowAIDrawer(!showAIDrawer)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
              showAIDrawer
                ? 'bg-amber-500 border-amber-600 text-slate-950 font-bold'
                : 'bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>AI Assistant</span>
          </button>

          {/* Export / Report links */}
          <a
            href={getPdfReportUrl(surveyId)}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 px-3 py-1 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-2xs transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>PDF Dossier</span>
          </a>

          <a
            href={getExportUrl(surveyId, 'geojson')}
            download
            className="flex items-center gap-1 px-3 py-1 bg-gov-50 border border-gov-200 hover:bg-gov-100 text-gov-700 rounded-lg text-xs font-semibold shadow-2xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>GeoJSON</span>
          </a>
        </div>
      </div>

      {/* Map + Sidebar Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Layer Switcher & Parcel List Drawer */}
        <div className="w-72 bg-white border-r border-slate-200 flex flex-col shrink-0 z-20 overflow-hidden">
          {/* Layer toggles panel */}
          <div className="p-3 border-b border-slate-200 bg-slate-50/70 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Geospatial Overlays
              </span>
              {/* Base map switcher */}
              <div className="flex items-center gap-1 bg-white border border-slate-200 rounded p-0.5 text-[10px]">
                <button
                  onClick={() => setBaseMap('satellite')}
                  className={`px-1.5 py-0.5 rounded font-medium ${
                    baseMap === 'satellite' ? 'bg-gov-600 text-white' : 'text-slate-600'
                  }`}
                >
                  Satellite
                </button>
                <button
                  onClick={() => setBaseMap('streets')}
                  className={`px-1.5 py-0.5 rounded font-medium ${
                    baseMap === 'streets' ? 'bg-gov-600 text-white' : 'text-slate-600'
                  }`}
                >
                  Streets
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showParcels}
                  onChange={(e) => setShowParcels(e.target.checked)}
                  className="rounded text-gov-600"
                />
                <span>AI Parcels ({parcels.length})</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showCadastral}
                  onChange={(e) => setShowCadastral(e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span>Legacy Map</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBuildings}
                  onChange={(e) => setShowBuildings(e.target.checked)}
                  className="rounded text-orange-600"
                />
                <span>Buildings</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showRoads}
                  onChange={(e) => setShowRoads(e.target.checked)}
                  className="rounded text-slate-600"
                />
                <span>Road Network</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showWater}
                  onChange={(e) => setShowWater(e.target.checked)}
                  className="rounded text-cyan-600"
                />
                <span>Water Bodies</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showDiscrepancies}
                  onChange={(e) => setShowDiscrepancies(e.target.checked)}
                  className="rounded text-rose-600"
                />
                <span>Discrepancies</span>
              </label>
            </div>
          </div>

          {/* Parcel Search / List Header */}
          <div className="p-2 border-b border-slate-200 flex items-center justify-between text-xs font-bold text-slate-700 bg-white">
            <span>Parcels Registry ({filteredParcels.length})</span>
            {highlightedParcelIds.length > 0 && (
              <button
                onClick={() => setHighlightedParcelIds([])}
                className="text-[10px] text-rose-600 hover:underline"
              >
                Clear AI Filter
              </button>
            )}
          </div>

          {/* Scrollable Parcel List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {filteredParcels.map((p) => {
              const isSelected = selectedParcel?.id === p.id;
              const isHighlighted = highlightedParcelIds.includes(p.parcel_id);

              return (
                <div
                  key={p.id}
                  onClick={() => handleSelectParcel(p)}
                  className={`p-3 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-gov-50/80 border-l-4 border-gov-600'
                      : isHighlighted
                      ? 'bg-amber-50/60 border-l-4 border-amber-500'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-gov-600" />
                      {p.parcel_id}
                    </span>
                    <StatusBadge status={p.status} size="xs" />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>{p.land_use}</span>
                    <span className="font-mono font-semibold text-slate-700">
                      {p.area_acres.toFixed(2)} ac
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-1.5 pt-1 border-t border-slate-100">
                    <ConfidenceBadge score={p.confidence} />
                    {p.discrepancy && (
                      <span className="text-[10px] font-bold text-rose-600 flex items-center gap-0.5">
                        <AlertTriangle className="w-3 h-3" />
                        {p.discrepancy.difference_distance}m shift
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center: Interactive Leaflet Map */}
        <div className="flex-1 h-full relative">
          {/* Editing Mode Banner */}
          {isEditing && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 z-40 bg-slate-900/95 text-white px-5 py-2.5 rounded-full shadow-2xl flex items-center gap-4 border border-slate-700 animate-in fade-in slide-in-from-top-4">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping"></span>
                <span className="text-xs font-bold">
                  Editing Boundary: {selectedParcel?.parcel_id}
                </span>
                <span className="text-[11px] text-slate-400 hidden sm:inline">
                  (Drag blue pins to adjust parcel corner vertices)
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setShowCommitModal(true)}
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors"
                >
                  Commit Adjustment
                </button>
              </div>
            </div>
          )}

          {/* Mouse Coordinate & Scale Box */}
          <div className="absolute bottom-2 left-2 z-30 bg-slate-900/80 backdrop-blur-xs text-white px-2.5 py-1 rounded-md text-[10px] font-mono shadow-md pointer-events-none">
            Lat: {mouseCoords.lat.toFixed(5)}, Lon: {mouseCoords.lng.toFixed(5)} | Datum: WGS84
          </div>

          {/* Leaflet Map Container */}
          <MapContainer
            center={defaultCenter}
            zoom={16}
            className="w-full h-full"
            zoomControl={false}
          >
            {/* Tile Layer */}
            {baseMap === 'satellite' ? (
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution="&copy; Esri &mdash; World Imagery"
                maxZoom={19}
              />
            ) : (
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap contributors"
                maxZoom={19}
              />
            )}

            <CoordinateTracker onCoordinatesChange={setMouseCoords} />
            {flyTarget && <MapFlyTo targetCoords={flyTarget} />}

            {/* 1. Cadastral Features (Buildings, Roads, Water Bodies) */}
            {showWater &&
              features
                .filter((f) => f.feature_type === 'water_body')
                .map((f, i) => {
                  if (f.geometry?.type === 'Polygon') {
                    const latlngs = f.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
                    return (
                      <Polygon
                        key={`water-${i}`}
                        positions={latlngs}
                        pathOptions={{
                          color: '#06b6d4',
                          fillColor: '#0891b2',
                          fillOpacity: 0.5,
                          weight: 2,
                        }}
                      >
                        <Popup>
                          <div className="p-2 text-xs">
                            <p className="font-bold text-cyan-800">Water Body / Village Pond</p>
                            <p className="text-[10px] text-slate-500">Feature Confidence: 99%</p>
                          </div>
                        </Popup>
                      </Polygon>
                    );
                  }
                  return null;
                })}

            {showBuildings &&
              features
                .filter((f) => f.feature_type === 'building')
                .map((f, i) => {
                  if (f.geometry?.type === 'Polygon') {
                    const latlngs = f.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
                    return (
                      <Polygon
                        key={`bldg-${i}`}
                        positions={latlngs}
                        pathOptions={{
                          color: '#ea580c',
                          fillColor: '#f97316',
                          fillOpacity: 0.6,
                          weight: 1.5,
                        }}
                      >
                        <Popup>
                          <div className="p-2 text-xs">
                            <p className="font-bold text-orange-800">Detected Structure / Homestead</p>
                            <p className="text-[10px] text-slate-500">AI YOLO Confidence: 94%</p>
                          </div>
                        </Popup>
                      </Polygon>
                    );
                  }
                  return null;
                })}

            {showRoads &&
              features
                .filter((f) => f.feature_type === 'road' || f.feature_type === 'pathway')
                .map((f, i) => {
                  if (f.geometry?.type === 'LineString') {
                    const latlngs = f.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
                    return (
                      <Polyline
                        key={`road-${i}`}
                        positions={latlngs}
                        pathOptions={{
                          color: '#475569',
                          weight: 4,
                          dashArray: '6, 4',
                        }}
                      />
                    );
                  }
                  return null;
                })}

            {/* 2. Existing Legacy Cadastral Boundaries (Dashed Blue Lines) */}
            {showCadastral &&
              discrepancies.map((d, i) => {
                if (d.old_geometry?.type === 'Polygon') {
                  const latlngs = d.old_geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
                  return (
                    <Polygon
                      key={`cadastral-${i}`}
                      positions={latlngs}
                      pathOptions={{
                        color: '#2563eb',
                        dashArray: '5, 5',
                        fillOpacity: 0.05,
                        fillColor: '#3b82f6',
                        weight: 2,
                      }}
                    />
                  );
                }
                return null;
              })}

            {/* 3. AI Detected Parcels */}
            {showParcels &&
              filteredParcels.map((p) => {
                const isSelected = selectedParcel?.id === p.id;
                const isHighlighted = highlightedParcelIds.includes(p.parcel_id);

                // Determine border color and fill by status
                let strokeColor = '#3b82f6';
                let fillColor = '#3b82f6';

                if (p.status === 'verified') {
                  strokeColor = '#10b981';
                  fillColor = '#10b981';
                } else if (p.status === 'flagged_discrepancy') {
                  strokeColor = '#f43f5e';
                  fillColor = '#f43f5e';
                } else if (p.confidence < 0.85) {
                  strokeColor = '#f59e0b';
                  fillColor = '#f59e0b';
                }

                if (isHighlighted) {
                  strokeColor = '#fbbf24';
                  fillColor = '#fef08a';
                }

                if (p.geometry?.type === 'Polygon') {
                  const latlngs = p.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);

                  return (
                    <Polygon
                      key={`parcel-${p.id}`}
                      positions={latlngs}
                      pathOptions={{
                        color: isSelected ? '#ffffff' : strokeColor,
                        fillColor: fillColor,
                        fillOpacity: isSelected ? 0.35 : 0.2,
                        weight: isSelected ? 3.5 : 2,
                      }}
                      eventHandlers={{
                        click: () => handleSelectParcel(p),
                      }}
                    >
                      <Popup>
                        <div className="p-2.5 text-xs space-y-1">
                          <p className="font-bold text-slate-900">{p.parcel_id}</p>
                          <p className="text-slate-600">{p.land_use}</p>
                          <p className="font-mono text-slate-700">Area: {p.area_acres.toFixed(2)} acres</p>
                          <div className="pt-1">
                            <StatusBadge status={p.status} size="xs" />
                          </div>
                        </div>
                      </Popup>
                    </Polygon>
                  );
                }
                return null;
              })}

            {/* 4. Active Vertex Editing Overlays */}
            {isEditing && editableCoords.length > 0 && (
              <>
                {/* Dotted Original AI Boundary Baseline */}
                {selectedParcel?.original_geometry?.coordinates && (
                  <Polygon
                    positions={selectedParcel.original_geometry.coordinates[0].map(([lng, lat]) => [
                      lat,
                      lng,
                    ])}
                    pathOptions={{
                      color: '#94a3b8',
                      dashArray: '4, 4',
                      weight: 2,
                      fillOpacity: 0.05,
                    }}
                  />
                )}

                {/* Solid Adjusted Boundary */}
                <Polygon
                  positions={editableCoords}
                  pathOptions={{
                    color: '#0284c7',
                    weight: 3,
                    fillColor: '#38bdf8',
                    fillOpacity: 0.3,
                  }}
                />

                {/* Draggable Vertex Pins */}
                {editableCoords.map((pt, idx) => (
                  <Marker
                    key={`vertex-${idx}`}
                    position={pt}
                    draggable={true}
                    icon={createVertexIcon()}
                    eventHandlers={{
                      drag: (e) => handleVertexDrag(idx, e),
                    }}
                  />
                ))}
              </>
            )}
          </MapContainer>

          {/* Floating AI Query Assistant Drawer (if open) */}
          {showAIDrawer && (
            <div className="absolute top-4 right-4 z-40 w-96 max-w-[calc(100vw-32px)] h-[480px]">
              <AIAssistantDrawer
                surveyId={surveyId}
                onHighlightParcels={setHighlightedParcelIds}
                onClose={() => setShowAIDrawer(false)}
              />
            </div>
          )}
        </div>

        {/* Right Side: Parcel Inspection & Verification Panel */}
        <div className="w-80 bg-white border-l border-slate-200 flex flex-col shrink-0 z-20 overflow-y-auto">
          {selectedParcel ? (
            <div className="p-4 space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Parcel Dossier
                  </span>
                  <h3 className="font-bold text-lg text-slate-900">{selectedParcel.parcel_id}</h3>
                </div>
                <StatusBadge status={selectedParcel.status} />
              </div>

              {/* Confidence Meter */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-medium">AI Confidence Score</span>
                  <ConfidenceBadge score={selectedParcel.confidence} />
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gov-600 rounded-full"
                    style={{ width: `${Math.round(selectedParcel.confidence * 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Spatial Geometry Properties */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Land Use:</span>
                  <span className="font-semibold text-slate-800">{selectedParcel.land_use}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Area (Acres):</span>
                  <span className="font-mono font-bold text-gov-700">
                    {selectedParcel.area_acres.toFixed(3)} acres
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Area (Metric):</span>
                  <span className="font-mono text-slate-700">
                    {selectedParcel.area.toLocaleString()} m²
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Perimeter:</span>
                  <span className="font-mono text-slate-700">
                    {selectedParcel.perimeter.toFixed(1)} meters
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Centroid:</span>
                  <span className="font-mono text-[11px] text-slate-600">
                    {selectedParcel.centroid_lat.toFixed(5)}, {selectedParcel.centroid_lon.toFixed(5)}
                  </span>
                </div>
              </div>

              {/* Legacy Cadastral Discrepancy Card */}
              {selectedParcel.discrepancy ? (
                <div className="p-3.5 bg-rose-50/70 border border-rose-200 rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-rose-800 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Cadastral Screening Discrepancy</span>
                  </div>
                  <p className="text-[11px] text-rose-900 leading-relaxed font-medium">
                    {selectedParcel.discrepancy.notes ||
                      'Variation detected between legacy map and drone boundary.'}
                  </p>

                  <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                    <div className="bg-white p-2 rounded-lg border border-rose-200">
                      <span className="text-slate-500 block">Boundary Shift</span>
                      <span className="font-bold text-rose-700 text-xs">
                        {selectedParcel.discrepancy.difference_distance} meters
                      </span>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-rose-200">
                      <span className="text-slate-500 block">Area Delta</span>
                      <span className="font-bold text-rose-700 text-xs">
                        {selectedParcel.discrepancy.difference_percentage}%
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center gap-2 text-emerald-800 text-xs font-medium">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Conforms to legacy revenue cadastral alignment.</span>
                </div>
              )}

              {/* Survey Officer Verification Actions */}
              <div className="pt-2 space-y-2">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Officer Adjudication
                </p>

                {/* Edit Boundary Button */}
                {!isEditing ? (
                  <button
                    onClick={startEditing}
                    className="w-full py-2 px-3 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs rounded-lg shadow-2xs transition-colors flex items-center justify-center gap-2"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-gov-600" />
                    <span>Edit Boundary Vertices</span>
                  </button>
                ) : (
                  <button
                    onClick={cancelEditing}
                    className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition-colors"
                  >
                    Exit Edit Mode
                  </button>
                )}

                {/* Verify / Reject Action Buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={handleVerify}
                    className="py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg shadow-sm transition-colors flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve</span>
                  </button>

                  <button
                    onClick={handleReject}
                    className="py-2 px-3 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-lg shadow-sm transition-colors flex items-center justify-center gap-1.5"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 space-y-2 my-auto">
              <MapPin className="w-8 h-8 mx-auto stroke-1" />
              <p className="text-xs font-medium">Click on any parcel polygon to view detailed cadastral dossier.</p>
            </div>
          )}
        </div>
      </div>

      {/* Human-in-the-loop Justification Modal */}
      <BoundaryEditorModal
        isOpen={showCommitModal}
        onClose={() => setShowCommitModal(false)}
        onSave={handleSaveGeometry}
        parcel={selectedParcel}
        originalArea={selectedParcel?.area_acres}
        adjustedArea={selectedParcel?.area_acres}
        saving={savingEdit}
      />
    </div>
  );
}
