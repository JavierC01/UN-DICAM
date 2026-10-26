import { apiRequest } from './client';

export function listProjects() {
  return apiRequest('/projects', { fallbackMessage: 'No fue posible obtener los proyectos.' });
}

export function createProject(name) {
  return apiRequest('/projects', {
    method: 'POST',
    body: { name },
    fallbackMessage: 'No fue posible crear el proyecto.',
  });
}

export function deleteProject(projectId) {
  return apiRequest(`/projects/${projectId}`, {
    method: 'DELETE',
    fallbackMessage: 'No fue posible eliminar el proyecto.',
  });
}

export function listProjectAnalyses(projectId) {
  return apiRequest(`/projects/${projectId}/analyses`, {
    fallbackMessage: 'No fue posible obtener el historial de analisis.',
  });
}
