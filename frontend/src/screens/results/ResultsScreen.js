import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { ApiError } from '../../api/client';
import { cancelAnalysis, getAnalysisResults, getAnalysisStatus } from '../../api/analysis';
import { ROUTES } from '../../navigation/routes';

const TERMINAL_STATUSES = ['success', 'failure', 'revoked'];
const POLL_INTERVAL_MS = 1500;

export default function ResultsScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName, taskId } = route.params || {};

  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [resultsPending, setResultsPending] = useState(false);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!taskId) return undefined;

    const poll = async () => {
      try {
        const current = await getAnalysisStatus(taskId);
        setStatus(current);
        if (TERMINAL_STATUSES.includes(current.status)) {
          clearInterval(intervalRef.current);
          if (current.status === 'success') {
            fetchResults();
          }
        }
      } catch (err) {
        setError(err.message || 'No fue posible consultar el estado del analisis.');
        clearInterval(intervalRef.current);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [taskId]);

  const fetchResults = async () => {
    try {
      const data = await getAnalysisResults(taskId);
      setResults(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 501) {
        setResultsPending(true);
      } else {
        setError(err.message || 'No fue posible obtener los resultados.');
      }
    }
  };

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await cancelAnalysis(taskId);
      clearInterval(intervalRef.current);
      setStatus((prev) => (prev ? { ...prev, status: 'revoked', mensaje: 'Analisis cancelado' } : prev));
    } catch (err) {
      setError(err.message || 'No fue posible cancelar el analisis.');
    } finally {
      setCancelling(false);
    }
  };

  if (!taskId) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Resultados</Text>
        <View style={styles.card}>
          <Text style={styles.label}>Sin analisis en curso</Text>
          <Text style={styles.value}>Inicia un analisis desde la definicion de la malla de rastreo.</Text>
        </View>
      </ScrollView>
    );
  }

  const inProgress = status && !TERMINAL_STATUSES.includes(status.status);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Resultados</Text>
      <Text style={styles.subtitle}>{projectName}</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.label}>Estado del analisis</Text>
        <Text style={styles.value}>{status ? status.status : 'Consultando...'}</Text>
        {status ? (
          <>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${Math.min(100, Math.max(0, status.progress))}%` }]} />
            </View>
            <Text style={styles.meta}>
              {status.frames_procesados}/{status.frames_total} frames · {status.progress}%
            </Text>
            <Text style={styles.meta}>{status.mensaje}</Text>
          </>
        ) : (
          <ActivityIndicator color="#1f6feb" style={styles.loading} />
        )}
      </View>

      {inProgress ? (
        <TouchableOpacity style={styles.cancelButton} onPress={handleCancel} disabled={cancelling}>
          {cancelling ? <ActivityIndicator color="#c0392b" /> : <Text style={styles.cancelText}>Cancelar analisis</Text>}
        </TouchableOpacity>
      ) : null}

      {resultsPending ? (
        <View style={styles.pendingBox}>
          <Text style={styles.pendingTitle}>Resultados aun no disponibles</Text>
          <Text style={styles.pendingText}>
            El backend todavia no expone el calculo completo de resultados (pipeline DIC en desarrollo). El
            analisis se ejecuto correctamente, pero la consulta de resultados detallados esta pendiente.
          </Text>
        </View>
      ) : null}

      {results ? (
        <View style={styles.card}>
          <Text style={styles.label}>Resumen</Text>
          <Text style={styles.value}>Esfuerzo maximo: {results.esfuerzo_max_mpa.toFixed(2)} MPa</Text>
          <Text style={styles.value}>Deformacion maxima: {results.strain_max.toFixed(4)}</Text>
          <Text style={styles.value}>Coef. correlacion medio: {results.coef_correlacion_medio.toFixed(3)}</Text>
        </View>
      ) : null}

      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate(ROUTES.REPORTS, { projectId })}>
        <Text style={styles.buttonText}>Ver reportes</Text>
      </TouchableOpacity>
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
    fontSize: 28,
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
  card: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
    marginBottom: 14,
  },
  label: {
    color: '#5d6d7e',
    marginBottom: 6,
  },
  value: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
    marginBottom: 4,
  },
  loading: {
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  progressTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#e5eaf0',
    marginTop: 10,
    overflow: 'hidden',
  },
  progressFill: {
    height: 8,
    backgroundColor: '#1f6feb',
  },
  meta: {
    marginTop: 8,
    color: '#5d6d7e',
    fontSize: 13,
  },
  cancelButton: {
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fdecea',
    borderWidth: 1,
    borderColor: '#f5c6cb',
    marginBottom: 14,
  },
  cancelText: {
    color: '#c0392b',
    fontWeight: '700',
  },
  pendingBox: {
    borderRadius: 8,
    padding: 16,
    backgroundColor: '#fff8e6',
    borderWidth: 1,
    borderColor: '#f0dca0',
    marginBottom: 14,
  },
  pendingTitle: {
    fontWeight: '700',
    color: '#8a6d1c',
    marginBottom: 6,
  },
  pendingText: {
    color: '#8a6d1c',
  },
  button: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
    marginTop: 6,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
});
