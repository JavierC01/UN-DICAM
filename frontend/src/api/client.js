import { API_BASE_URL } from '../config/api';
import { clearToken, getToken } from './session';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export class NotFoundError extends ApiError {}

let onUnauthorized = null;

// La navegacion registra aqui como volver al login cuando la sesion expira.
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

async function parseErrorMessage(response, fallback) {
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
    // el cuerpo no era JSON, se usa el mensaje por defecto
  }
  return fallback;
}

export async function apiRequest(path, { method = 'GET', body, fallbackMessage } = {}) {
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData;
  const headers = {};
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError('No fue posible conectar con el servidor. Verifica tu conexion.', 0);
  }

  if (!response.ok) {
    const message = await parseErrorMessage(response, fallbackMessage || 'Ocurrio un error inesperado.');
    if (response.status === 401 && token) {
      await clearToken();
      onUnauthorized?.();
    }
    if (response.status === 404) {
      throw new NotFoundError(message, response.status);
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

// URL de descarga que se abre fuera de la app (navegador): el token va como parametro.
export function authenticatedUrl(path) {
  const separator = path.includes('?') ? '&' : '?';
  return `${API_BASE_URL}${path}${separator}token=${encodeURIComponent(getToken() || '')}`;
}

// Los mapas se sirven en /storage, fuera de /api/v1.
export function storageUrl(path) {
  return `${API_BASE_URL.replace(/\/api\/v1\/?$/, '')}${path}`;
}

// Archivo elegido con expo-document-picker o grabado con expo-camera -> parte de un FormData.
export function fileFormPart(asset, fallbackName, fallbackType) {
  if (asset.file) return asset.file; // web: el picker entrega un File
  return { uri: asset.uri, name: asset.name || fallbackName, type: asset.mimeType || fallbackType };
}
