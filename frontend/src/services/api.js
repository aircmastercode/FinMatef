import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// User API endpoints
export const userApi = {
  // Query endpoints
  submitQuery: (query, userId, sessionId) => 
    api.post('/user/query/', { query, user_id: userId, session_id: sessionId }),
  
  // Voice endpoints
  uploadVoice: (formData) => 
    api.post('/user/voice/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  // History endpoints
  getHistory: (userId, sessionId, limit = 20, offset = 0) => 
    api.get(`/user/history/?user_id=${userId}&session_id=${sessionId}&limit=${limit}&offset=${offset}`),
  
  getSessions: (userId) => 
    api.get(`/user/history/sessions?user_id=${userId}`),
  
  deleteHistory: (userId, sessionId) => 
    api.delete(`/user/history/?user_id=${userId}&session_id=${sessionId}`),
};

// Admin API endpoints
export const adminApi = {
  // Document endpoints
  uploadDocument: (formData) => 
    api.post('/admin/document/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  uploadText: (formData) => 
    api.post('/admin/document/text', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  // Knowledge endpoints
  getKnowledge: () => 
    api.get('/admin/knowledge/'),
  
  // Escalation endpoints
  getEscalations: () => 
    api.get('/admin/escalation/'),
  
  resolveEscalation: (escalationId, resolution, userId, sessionId) => 
    api.post('/admin/escalation/resolve', { 
      escalation_id: escalationId, 
      resolution, 
      user_id: userId, 
      session_id: sessionId 
    }),
};

// System API endpoints
export const systemApi = {
  getHealth: () => 
    api.get('/health'),
  
  getSystemInfo: () => 
    api.get('/system/info'),
};

export default api; 