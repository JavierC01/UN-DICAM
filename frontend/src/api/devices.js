import { apiRequest, fileFormPart } from './client';

export function listCameras() {
  return apiRequest('/devices/cameras', { fallbackMessage: 'No fue posible listar las camaras.' });
}

export function openDevice(payload) {
  return apiRequest('/devices/open', {
    method: 'POST',
    body: payload,
    fallbackMessage: 'No fue posible abrir la fuente de video.',
  });
}

export function getFirstFrame(sourceId) {
  return apiRequest(`/devices/frame/${sourceId}`, {
    fallbackMessage: 'No fue posible obtener el primer frame.',
  });
}

export function uploadVideo(asset) {
  const form = new FormData();
  form.append('file', fileFormPart(asset, 'video.mp4', 'video/mp4'));
  return apiRequest('/devices/upload', {
    method: 'POST',
    body: form,
    fallbackMessage: 'No fue posible subir el video.',
  });
}
