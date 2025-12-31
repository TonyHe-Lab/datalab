import api from './api';
import type { DiagnosisRequest, DiagnosisResponse, ReferenceCase } from '../types/api';

export const chatService = {
  async diagnose(request: DiagnosisRequest): Promise<DiagnosisResponse> {
    const response = await api.post<DiagnosisResponse>('/chat', request);
    return response.data;
  },
};

export const searchService = {
  async searchSimilarCases(query: string): Promise<ReferenceCase[]> {
    const response = await api.get<ReferenceCase[]>('/search', {
      params: { query },
    });
    return response.data;
  },
};
