import { API_BASE_URL } from '../config/api';

export class InvalidCredentialsError extends Error {}
export class EmailAlreadyRegisteredError extends Error {}

export async function login(email, password) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new Error('No fue posible conectar con el servidor. Verifica tu conexion.');
  }

  if (response.status === 401) {
    throw new InvalidCredentialsError(
      'Las credenciales no se encuentran en la base de datos de usuarios registrados.'
    );
  }
  if (!response.ok) {
    throw new Error('No fue posible iniciar sesion. Intenta nuevamente.');
  }
  return response.json();
}

export async function register(fullName, email, password) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password }),
    });
  } catch {
    throw new Error('No fue posible conectar con el servidor. Verifica tu conexion.');
  }

  if (response.status === 409) {
    throw new EmailAlreadyRegisteredError('Ese correo ya se encuentra registrado.');
  }
  if (!response.ok) {
    throw new Error('No fue posible crear la cuenta. Intenta nuevamente.');
  }
  return response.json();
}
