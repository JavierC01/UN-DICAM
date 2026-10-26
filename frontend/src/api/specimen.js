import { apiRequest } from './client';

export function getSpecimen(projectId) {
  return apiRequest(`/specimen/${projectId}`, {
    fallbackMessage: 'No fue posible obtener la configuracion de la probeta.',
  });
}

export function configureSpecimen(payload) {
  return apiRequest('/specimen/configure', {
    method: 'POST',
    body: payload,
    fallbackMessage: 'No fue posible guardar la configuracion de la probeta.',
  });
}

export function listTestTypes() {
  return apiRequest('/specimen/ensayos', { fallbackMessage: 'No fue posible obtener los tipos de ensayo.' });
}
