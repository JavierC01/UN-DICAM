import { apiRequest } from './client';

export function validateMesh(payload) {
  return apiRequest('/tracking/validate', {
    method: 'POST',
    body: payload,
    fallbackMessage: 'No fue posible validar el poligono.',
  });
}

export function buildMesh(payload) {
  return apiRequest('/tracking/mesh', {
    method: 'POST',
    body: payload,
    fallbackMessage: 'No fue posible construir la malla de rastreo.',
  });
}
