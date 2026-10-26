import { apiRequest, ApiError } from './client';
import { clearToken, saveToken } from './session';

export class InvalidCredentialsError extends Error {}
export class EmailAlreadyRegisteredError extends Error {}

export async function login(email, password) {
  try {
    const session = await apiRequest('/auth/login', {
      method: 'POST',
      body: { email, password },
      fallbackMessage: 'No fue posible iniciar sesion. Intenta nuevamente.',
    });
    await saveToken(session.access_token);
    return session.user;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      throw new InvalidCredentialsError(
        'Las credenciales no se encuentran en la base de datos de usuarios registrados.'
      );
    }
    throw err;
  }
}

export function logout() {
  return clearToken();
}

export async function register(fullName, email, password) {
  try {
    return await apiRequest('/auth/register', {
      method: 'POST',
      body: { full_name: fullName, email, password },
      fallbackMessage: 'No fue posible crear la cuenta. Intenta nuevamente.',
    });
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      throw new EmailAlreadyRegisteredError('Ese correo ya se encuentra registrado.');
    }
    throw err;
  }
}
