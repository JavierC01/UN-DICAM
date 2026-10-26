import { apiRequest, authenticatedUrl } from './client';

export function startAnalysis(payload) {
  return apiRequest('/analysis/start', {
    method: 'POST',
    body: payload,
    fallbackMessage: 'No fue posible iniciar el analisis.',
  });
}

export function getAnalysisStatus(taskId) {
  return apiRequest(`/analysis/status/${taskId}`, {
    fallbackMessage: 'No fue posible consultar el estado del analisis.',
  });
}

export function getAnalysisResults(analysisId) {
  return apiRequest(`/analysis/results/${analysisId}`, {
    fallbackMessage: 'No fue posible obtener los resultados.',
  });
}

export function cancelAnalysis(analysisId) {
  return apiRequest(`/analysis/${analysisId}`, {
    method: 'DELETE',
    fallbackMessage: 'No fue posible cancelar el analisis.',
  });
}

export function fitProperty(analysisId, range) {
  return apiRequest(`/analysis/${analysisId}/propiedad`, {
    method: 'POST',
    body: range,
    fallbackMessage: 'No fue posible ajustar la propiedad.',
  });
}

export function exportUrl(format, analysisId) {
  return authenticatedUrl(`/export/${format}/${analysisId}`);
}
