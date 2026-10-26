import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Linking, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { exportUrl } from '../../api/analysis';
import { listProjectAnalyses, listProjects } from '../../api/projects';
import { ROUTES } from '../../navigation/routes';
import { colors, radii, spacing, touchTarget, typography } from '../../styles/theme';

const STATUS_LABELS = {
  pending: 'En cola',
  running: 'Procesando',
  success: 'Completado',
  failed: 'Fallo',
  revoked: 'Cancelado',
};
const FORMATS = [
  { key: 'csv', label: 'CSV (datos por frame)' },
  { key: 'pdf', label: 'PDF (reporte tecnico)' },
  { key: 'jpg', label: 'JPG (curvas y mapas)' },
];

function formatDate(isoString) {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleString();
  } catch {
    return '';
  }
}

export default function ReportsScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const [project, setProject] = useState(
    route.params?.projectId ? { id: route.params.projectId, name: route.params.projectName } : null
  );
  const [projects, setProjects] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      setLoading(true);
      setError('');
      (project ? listProjectAnalyses(project.id) : listProjects())
        .then((data) => {
          if (cancelled) return;
          if (project) setAnalyses(data);
          else setProjects(data);
        })
        .catch((err) => !cancelled && setError(err.message || 'No fue posible cargar los datos.'))
        .finally(() => !cancelled && setLoading(false));
      return () => {
        cancelled = true;
      };
    }, [project])
  );

  const handleDownload = async (format, analysisId) => {
    try {
      await Linking.openURL(exportUrl(format, analysisId));
    } catch {
      setError('No fue posible abrir la descarga en este dispositivo.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Reportes</Text>
      {project ? (
        <View style={styles.header}>
          <Text style={styles.subtitle}>{project.name}</Text>
          <TouchableOpacity onPress={() => setProject(null)} accessibilityRole="button">
            <Text style={styles.link}>Cambiar proyecto</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <Text style={styles.subtitle}>Elige un proyecto para ver su historial de analisis.</Text>
      )}

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {loading ? <ActivityIndicator color={colors.primary} /> : null}

      {!loading && !project
        ? projects.map((p) => (
            <TouchableOpacity key={p.id} style={styles.card} onPress={() => setProject(p)} accessibilityRole="button">
              <Text style={styles.cardTitle}>{p.name}</Text>
            </TouchableOpacity>
          ))
        : null}

      {!loading && project && analyses.length === 0 ? (
        <Text style={styles.cardText}>Este proyecto aun no tiene analisis.</Text>
      ) : null}

      {!loading && project
        ? analyses.map((a) => (
            <View key={a.id} style={styles.card}>
              <Text style={styles.cardTitle}>
                {formatDate(a.created_at)} · {STATUS_LABELS[a.status] || a.status}
              </Text>
              <Text style={styles.cardText}>
                Subset {a.params?.subset_size} px · busqueda {a.params?.search_range} px
              </Text>
              {a.status === 'success' ? (
                <>
                  <TouchableOpacity
                    style={styles.secondaryButton}
                    onPress={() =>
                      navigation.navigate(ROUTES.RESULTS, { projectId: project.id, projectName: project.name, taskId: a.id })
                    }
                  >
                    <Text style={styles.secondaryButtonText}>Ver resultados</Text>
                  </TouchableOpacity>
                  {FORMATS.map((f) => (
                    <TouchableOpacity
                      key={f.key}
                      style={styles.button}
                      onPress={() => handleDownload(f.key, a.id)}
                      accessibilityRole="link"
                      accessibilityLabel={`Descargar ${f.label}`}
                    >
                      <Text style={styles.buttonText}>Descargar {f.label}</Text>
                    </TouchableOpacity>
                  ))}
                </>
              ) : null}
            </View>
          ))
        : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: spacing.lg,
    backgroundColor: colors.background,
  },
  title: {
    fontSize: typography.title,
    fontWeight: '700',
    color: colors.text,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subtitle: {
    marginTop: spacing.xs,
    marginBottom: spacing.md,
    color: colors.mutedText,
  },
  link: {
    color: colors.primary,
    fontWeight: '700',
    padding: spacing.sm,
  },
  errorBox: {
    borderWidth: 1,
    borderColor: colors.dangerBorder,
    backgroundColor: colors.dangerSoft,
    borderRadius: radii.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorText: {
    color: colors.danger,
    fontWeight: '600',
    textAlign: 'center',
  },
  card: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
    minHeight: touchTarget,
  },
  cardTitle: {
    fontSize: typography.body,
    fontWeight: '700',
    color: colors.text,
  },
  cardText: {
    marginTop: spacing.xs,
    marginBottom: spacing.sm,
    color: colors.mutedText,
  },
  button: {
    minHeight: touchTarget,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    marginTop: spacing.sm,
  },
  buttonText: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  secondaryButton: {
    minHeight: touchTarget,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
  },
  secondaryButtonText: {
    color: colors.primary,
    fontWeight: '700',
  },
});
