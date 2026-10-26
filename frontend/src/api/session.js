import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'undicam_token';
let token = null;

// expo-secure-store no funciona en web; ahi el token vive en localStorage.
const storage =
  Platform.OS === 'web'
    ? {
        getItemAsync: async (key) => globalThis.localStorage?.getItem(key) ?? null,
        setItemAsync: async (key, value) => globalThis.localStorage?.setItem(key, value),
        deleteItemAsync: async (key) => globalThis.localStorage?.removeItem(key),
      }
    : SecureStore;

export function getToken() {
  return token;
}

export async function saveToken(value) {
  token = value;
  await storage.setItemAsync(TOKEN_KEY, value);
}

export async function restoreToken() {
  token = await storage.getItemAsync(TOKEN_KEY);
  return token;
}

export async function clearToken() {
  token = null;
  await storage.deleteItemAsync(TOKEN_KEY);
}
