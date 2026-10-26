import { apiRequest, fileFormPart } from './client';

// Sin mapping devuelve solo las columnas del archivo (configurado: false).
export function importMachineFile(projectId, asset, mapping = {}) {
  const form = new FormData();
  form.append('file', fileFormPart(asset, 'carga.csv', 'text/csv'));
  Object.entries(mapping).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') form.append(key, String(value));
  });
  return apiRequest(`/loads/${projectId}/archivo`, {
    method: 'POST',
    body: form,
    fallbackMessage: 'No fue posible importar el archivo de carga.',
  });
}

export function getMachineLoad(projectId) {
  return apiRequest(`/loads/${projectId}`, {
    fallbackMessage: 'No fue posible consultar el archivo de carga.',
  });
}
