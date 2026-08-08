import { API_BASE_URL } from '../config/api';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export class NotFoundError extends ApiError {}

async function parseErrorMessage(response, fallback) {
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') return body.detail;
  } catch {
    // el cuerpo no era JSON, se usa el mensaje por defecto
  }
  return fallback;
}

export async function apiRequest(path, { method = 'GET', body, fallbackMessage } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError('No fue posible conectar con el servidor. Verifica tu conexion.', 0);
  }

  if (!response.ok) {
    const message = await parseErrorMessage(response, fallbackMessage || 'Ocurrio un error inesperado.');
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
