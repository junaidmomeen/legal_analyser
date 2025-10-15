import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
});

export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

interface KeyClause {
  type: string;
  content: string;
  importance: 'high' | 'medium' | 'low';
  classification: string;
  risk_score: number;
  page?: number;
  confidence: number;
}

export interface AnalysisResult {
  summary: string;
  key_clauses: KeyClause[];
  document_type: string;
  total_pages: number;
  confidence: number;
  processing_time: number;
  word_count: number;
  analyzed_at: string;
  file_id?: string;
}

// Backend now responds as { formats: string[] }
export interface SupportedFormats {
  formats: string[];
}

export const analyzeDocument = async (file: File, onUploadProgress: (progress: number) => void): Promise<AnalysisResult> => {
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await apiClient.post<AnalysisResult>('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw { 
        message: error.response.data.detail || 'Analysis failed.', 
        status: error.response.status,
        details: error.response.data
      } as ApiError;
    }
    throw { message: 'Analysis failed.' } as ApiError;
  }
};

export const exportAnalysis = async (fileId: string, format: 'pdf' | 'json', options: { timeout?: number } = {}) => {
  const { timeout = 120000 } = options; // 2-minute timeout
  const startTime = Date.now();

  try {
    // Start the export task
    const startExportResponse = await apiClient.post<{ task_id: string }>(`/export/${fileId}/${format}`);
    const taskId = startExportResponse.data.task_id;

    // Poll for completion
    while (Date.now() - startTime < timeout) {
      try {
        const pollResponse = await apiClient.get(`/export/${taskId}`);

        if (pollResponse.data.status === 'ready') {
          const downloadResponse = await apiClient.get(`/export/${taskId}/download`, {
            responseType: 'blob'
          });

          // Download the file
          const url = window.URL.createObjectURL(new Blob([downloadResponse.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `analysis-report.${format}`);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
          return;

        } else if (pollResponse.data.status === 'failed') {
          throw new Error('Export task failed');
        } else if (pollResponse.data.status === 'processing') {
          await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        } else {
          throw new Error(`Unknown export status: ${pollResponse.data.status}`);
        }
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          throw new Error('Export task not found');
        }
        throw error;
      }
    }

    throw new Error(`Export process timed out after ${timeout / 1000} seconds.`);
  } catch (error) {
    console.error('Export error:', error);
    if (axios.isAxiosError(error)) {
      const errorMessage = error.response?.data?.detail || error.message;
      throw new Error(`Export failed: ${errorMessage}`);
    }
    throw error;
  }
};

export const viewOriginalDocument = async (fileId: string) => {
  const response = await apiClient.get(`/documents/${fileId}`, { responseType: 'blob' });
  const fileURL = URL.createObjectURL(response.data);
  window.open(fileURL, '_blank');
};

export const getSupportedFormats = async (): Promise<SupportedFormats> => {
  const response = await apiClient.get<SupportedFormats>('/supported-formats');
  return response.data;
};

export const clearHistory = async (): Promise<{ message: string }> => {
    try {
      const response = await apiClient.delete('/analyses');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw { 
          message: error.response.data.detail || 'Failed to clear history.', 
          status: error.response.status,
          details: error.response.data
        } as ApiError;
      }
      throw { message: 'Failed to clear history.' } as ApiError;
    }
  };
