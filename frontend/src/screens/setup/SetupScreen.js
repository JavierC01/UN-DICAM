import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { configureSpecimen, getSpecimen } from '../../api/specimen';
import { NotFoundError } from '../../api/client';
import { ROUTES } from '../../navigation/routes';

const FIELDS = [
  { key: 'long_calibracion_px', label: 'Longitud de calibracion (px)' },
  { key: 'long_calibracion_mm', label: 'Longitud de calibracion (mm)' },
  { key: 'ancho_mm', label: 'Ancho de la probeta (mm)' },
  { key: 'espesor_mm', label: 'Espesor de la probeta (mm)' },
  { key: 'long_calibre_mm', label: 'Longitud de calibre (mm)' },
];

export default function SetupScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName } = route.params || {};

  const [values, setValues] = useState({
    long_calibracion_px: '',
    long_calibracion_mm: '',
    ancho_mm: '',
    espesor_mm: '',
    long_calibre_mm: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const existing = await getSpecimen(projectId);
        setSummary(existing);
      } catch (err) {
        if (!(err instanceof NotFoundError)) {
          setError(err.message || 'No fue posible cargar la configuracion existente.');
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId]);

  const handleChange = (key, text) => {
    setValues((prev) => ({ ...prev, [key]: text }));
  };

  const handleSave = async () => {
    if (!projectId) return;
    setError('');

    const parsed = {};
    for (const field of FIELDS) {
      const num = Number(values[field.key]);
      if (!values[field.key] || Number.isNaN(num) || num <= 0) {
        setError(`Ingresa un valor valido para "${field.label}".`);
        return;
      }
      parsed[field.key] = num;
    }

    setSaving(true);
    try {
      const response = await configureSpecimen({ project_id: projectId, ...parsed, roi_carga: null });
      setSummary(response);
    } catch (err) {
      setError(err.message || 'No fue posible guardar la configuracion.');
    } finally {
      setSaving(false);
    }
  };

  if (!projectId) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Selecciona un proyecto desde la lista para calibrar su probeta.</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator color="#1f6feb" />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Calibracion de probeta</Text>
      <Text style={styles.subtitle}>{projectName}</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {FIELDS.map((field) => (
        <View key={field.key} style={styles.field}>
          <Text style={styles.label}>{field.label}</Text>
          <TextInput
            style={styles.input}
            keyboardType="decimal-pad"
            value={values[field.key]}
            onChangeText={(text) => handleChange(field.key, text)}
            placeholder="0.0"
          />
        </View>
      ))}

      <TouchableOpacity style={styles.button} onPress={handleSave} disabled={saving}>
        {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Guardar calibracion</Text>}
      </TouchableOpacity>

      {summary ? (
        <View style={styles.summaryBox}>
          <Text style={styles.summaryTitle}>Calibracion confirmada</Text>
          <Text style={styles.summaryText}>px/mm: {summary.px_por_mm.toFixed(4)}</Text>
          <Text style={styles.summaryText}>mm/px: {summary.mm_por_px.toFixed(4)}</Text>
          <Text style={styles.summaryText}>Area: {summary.area_mm2.toFixed(2)} mm²</Text>
          <TouchableOpacity
            style={styles.nextButton}
            onPress={() => navigation.navigate(ROUTES.VIDEO_CAPTURE, { projectId, projectName })}
          >
            <Text style={styles.buttonText}>Continuar a captura de video</Text>
          </TouchableOpacity>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: '#f7f9fb',
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#17202a',
  },
  subtitle: {
    marginTop: 4,
    marginBottom: 18,
    color: '#5d6d7e',
  },
  errorBox: {
    borderWidth: 1,
    borderColor: '#f5c6cb',
    backgroundColor: '#fdecea',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#c0392b',
    fontWeight: '600',
    textAlign: 'center',
  },
  field: {
    marginBottom: 14,
  },
  label: {
    color: '#5d6d7e',
    marginBottom: 6,
    fontWeight: '600',
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: '#d6dde5',
    borderRadius: 8,
    paddingHorizontal: 14,
    backgroundColor: '#fff',
  },
  button: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  summaryBox: {
    marginTop: 20,
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#17202a',
    marginBottom: 8,
  },
  summaryText: {
    color: '#5d6d7e',
    marginBottom: 4,
  },
  nextButton: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2da44e',
    marginTop: 14,
  },
});
