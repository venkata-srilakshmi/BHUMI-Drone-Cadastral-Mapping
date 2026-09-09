import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bhoomi_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('bhoomi_token');
      localStorage.removeItem('bhoomi_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const loginUser = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Surveys
export const getSurveys = async () => {
  const response = await api.get('/surveys');
  return response.data;
};

export const getSurvey = async (id) => {
  const response = await api.get(`/surveys/${id}`);
  return response.data;
};

export const createSurvey = async (surveyData) => {
  const response = await api.post('/surveys', surveyData);
  return response.data;
};

export const uploadSurveyFiles = async (id, formData) => {
  const response = await api.post(`/surveys/${id}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const startSurveyProcessing = async (id) => {
  const response = await api.post(`/surveys/${id}/process`);
  return response.data;
};

export const getSurveyStatus = async (id) => {
  const response = await api.get(`/surveys/${id}/status`);
  return response.data;
};

export const loadDemoSurvey = async () => {
  const response = await api.post('/surveys/load-demo');
  return response.data;
};

// Parcels
export const getSurveyParcels = async (surveyId, params = {}) => {
  const response = await api.get(`/surveys/${surveyId}/parcels`, { params });
  return response.data;
};

export const getParcel = async (parcelId) => {
  const response = await api.get(`/parcels/${parcelId}`);
  return response.data;
};

export const updateParcelGeometry = async (parcelId, geometry, reason) => {
  const response = await api.put(`/parcels/${parcelId}/geometry`, { geometry, reason });
  return response.data;
};

export const verifyParcel = async (parcelId, reason) => {
  const response = await api.post(`/parcels/${parcelId}/verify`, { status: 'verified', reason });
  return response.data;
};

export const rejectParcel = async (parcelId, reason) => {
  const response = await api.post(`/parcels/${parcelId}/reject`, { status: 'rejected', reason });
  return response.data;
};

export const getParcelHistory = async (parcelId) => {
  const response = await api.get(`/parcels/${parcelId}/history`);
  return response.data;
};

// Features & Discrepancies
export const getSurveyFeatures = async (surveyId) => {
  const response = await api.get(`/surveys/${surveyId}/features`);
  return response.data;
};

export const getSurveyDiscrepancies = async (surveyId) => {
  const response = await api.get(`/surveys/${surveyId}/discrepancies`);
  return response.data;
};

// Change Detection
export const executeChangeDetection = async (surveyAId, surveyBId) => {
  const response = await api.post('/change-detection', {
    survey_a_id: surveyAId,
    survey_b_id: surveyBId,
  });
  return response.data;
};

export const getChangeDetectionRuns = async () => {
  const response = await api.get('/change-detection/runs');
  return response.data;
};

// AI Spatial Assistant Query
export const queryAIAssistant = async (surveyId, query) => {
  const response = await api.post(`/surveys/${surveyId}/ai-query`, { query });
  return response.data;
};

// Analytics Dashboard
export const getDashboardAnalytics = async () => {
  const response = await api.get('/analytics/dashboard');
  return response.data;
};

// Reports & Export URLs
export const getPdfReportUrl = (surveyId) => `/api/surveys/${surveyId}/report`;
export const getExportUrl = (surveyId, format) => `/api/surveys/${surveyId}/export/${format}`;

export default api;
