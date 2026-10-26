import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Image, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { cancelAnalysis, fitProperty, getAnalysisResults, getAnalysisStatus } from '../../api/analysis';
import { storageUrl } from '../../api/client';
import SegmentedControl from '../../components/molecules/SegmentedControl';
import CurveChart from '../../components/organisms/CurveChart';
import { ROUTES } from '../../navigation/routes';
import { colors, radii, spacing, typography } from '../../styles/theme';

const TERMINAL_STATUSES = ['success', 'failure', 'revoked'];
const POLL_INTERVAL_MS = 1500;
const STATUS_LABELS = {
  pending: 'En cola',
  started: 'Iniciado',
  progress: 'Procesando',
  success: 'Completado',
  failure: 'Fallo',
  revoked: 'Cancelado',
};
const RANGE_MODES = [
  { key: 'x', label: 'Rango de la medida (eje x)' },
  { key: 'fraccion', label: 'Fraccion de la respuesta maxima' },
];

const fmt = (value, digits = 4) => (value === null || value === undefined ? 'sin dato' : Number(value).toPrecision(digits));

// Extremos en x de los puntos que entraron al ajuste, para dibujar la recta solo sobre ese tramo.
function fitSegment(curve, ajuste) {
  if (!ajuste) return null;
  const { rango } = ajuste;
  const xs = curve.x.filter((x, i) => {
    const y = curve.y[i];
    if (!Number.isFinite(x) || !Number.isFinite(y)) return false;
    if (rango.tipo === 'x') return x >= rango.min && x <= rango.max;
    return y >= rango.min * rango.respuesta_max && y <= rango.max * rango.respuesta_max;
  });
  return xs.length ? { ...ajuste, xMin: Math.min(...xs), xMax: Math.max(...xs) } : null;
}

export default function ResultsScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName, taskId } = route.params || {};

  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [rangeMode, setRangeMode] = useState('x');
  const [range, setRange] = useState({ min: '', max: '' });
  const [fitting, setFitting] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!taskId) return undefined;

    const fetchResults = async () => {
      try {
        setResults(await getAnalysisResults(taskId));
      } catch (err) {
        setError(err.message || 'No fue posible obtener los resultados.');
      }
    };

    const poll = async () => {
      try {
        const current = await getAnalysisStatus(taskId);
        setStatus(current);
        if (TERMINAL_STATUSES.includes(current.status)) {
          clearInterval(intervalRef.current);
          if (current.status === 'success') fetchResults();
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

  const handleFit = async () => {
    setError('');
    const min = Number(range.min);
    const max = Number(range.max);
    if (range.min === '' || range.max === '' || Number.isNaN(min) || Number.isNaN(max) || min >= max) {
      setError('Ingresa un rango valido (minimo menor que maximo).');
      return;
    }
    setFitting(true);
    try {
      const body = rangeMode === 'x' ? { x_min: min, x_max: max } : { fraccion_min: min, fraccion_max: max };
      const ajuste = await fitProperty(taskId, body);
      setResults((prev) => ({ ...prev, ensayo: { ...prev.ensayo, ajuste } }));
    } catch (err) {
      setError(err.message || 'No fue posible ajustar la propiedad.');
    } finally {
      setFitting(false);
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
  const ensayo = results?.ensayo;

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
        <Text style={styles.value}>{status ? STATUS_LABELS[status.status] || status.status : 'Consultando...'}</Text>
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
          <ActivityIndicator color={colors.primary} style={styles.loading} />
        )}
      </View>

      {inProgress ? (
        <TouchableOpacity style={styles.cancelButton} onPress={handleCancel} disabled={cancelling}>
          {cancelling ? <ActivityIndicator color={colors.danger} /> : <Text style={styles.cancelText}>Cancelar analisis</Text>}
        </TouchableOpacity>
      ) : null}

      {results ? (
        <>
          {results.advertencias.length > 0 ? (
            <View style={styles.warningBox}>
              <Text style={styles.warningTitle}>Advertencias</Text>
              {results.advertencias.map((a) => (
                <Text key={a} style={styles.warningText}>
                  • {a}
                </Text>
              ))}
            </View>
          ) : null}

          <View style={styles.card}>
            <Text style={styles.label}>Resumen</Text>
            <Text style={styles.value}>Esfuerzo axial maximo: {fmt(results.esfuerzo_max_mpa)} MPa</Text>
            <Text style={styles.value}>Deformacion eps_yy maxima: {fmt(results.strain_max)}</Text>
            <Text style={styles.value}>Coef. correlacion medio: {fmt(results.coef_correlacion_medio, 3)}</Text>
            <Text style={styles.meta}>
              Carga: {results.carga.fuente} · {results.carga.frames_con_carga ?? 0} frames con carga
              {results.carga.fallos_ocr !== undefined ? ` · ${results.carga.fallos_ocr} fallos de OCR` : ''}
              {results.carga.descartados !== undefined
                ? ` · ${results.carga.interpolados} interpolados, ${results.carga.descartados} fuera del registro`
                : ''}
            </Text>
          </View>

          {ensayo ? (
            <>
              <CurveChart
                title={`Ensayo de ${ensayo.nombre}`}
                x={ensayo.curva.x}
                y={ensayo.curva.y}
                xLabel={`${ensayo.medida.nombre} [${ensayo.medida.unidad}]`}
                yLabel={`${ensayo.respuesta.nombre} [${ensayo.respuesta.unidad}]`}
                fit={fitSegment(ensayo.curva, ensayo.ajuste)}
              />
              <View style={styles.card}>
                <Text style={styles.label}>
                  {ensayo.propiedad.nombre}: elige el rango del ajuste lineal segun la norma aplicable
                </Text>
                <SegmentedControl options={RANGE_MODES} value={rangeMode} onChange={setRangeMode} />
                <View style={styles.rangeRow}>
                  <TextInput
                    style={styles.input}
                    keyboardType="numbers-and-punctuation"
                    placeholder={rangeMode === 'x' ? `min [${ensayo.medida.unidad}]` : 'min (p. ej. 0.1)'}
                    value={range.min}
                    onChangeText={(t) => setRange((prev) => ({ ...prev, min: t }))}
                    accessibilityLabel="Limite inferior del rango"
                  />
                  <TextInput
                    style={styles.input}
                    keyboardType="numbers-and-punctuation"
                    placeholder={rangeMode === 'x' ? `max [${ensayo.medida.unidad}]` : 'max (p. ej. 0.4)'}
                    value={range.max}
                    onChangeText={(t) => setRange((prev) => ({ ...prev, max: t }))}
                    accessibilityLabel="Limite superior del rango"
                  />
                </View>
                <TouchableOpacity style={styles.button} onPress={handleFit} disabled={fitting}>
                  {fitting ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.buttonText}>Calcular</Text>}
                </TouchableOpacity>
                {ensayo.ajuste ? (
                  <Text style={styles.value}>
                    {ensayo.propiedad.nombre}: {fmt(ensayo.ajuste.pendiente, 5)} {ensayo.propiedad.unidad} · R² ={' '}
                    {fmt(ensayo.ajuste.r2, 4)} · {ensayo.ajuste.n_puntos} puntos
                  </Text>
                ) : null}
              </View>
            </>
          ) : null}

          <CurveChart
            title="Carga - desplazamiento"
            x={results.curva_desplaz_carga.x}
            y={results.curva_desplaz_carga.y}
            xLabel="Desplazamiento nodo central [mm]"
            yLabel="Carga [N]"
          />
          <CurveChart
            title="Esfuerzo - deformacion"
            x={results.curva_esfuerzo_strain.x}
            y={results.curva_esfuerzo_strain.y}
            xLabel="eps_yy medio [-]"
            yLabel="Esfuerzo axial [MPa]"
          />

          <Text style={styles.label}>Mapas de deformacion (ultimo frame, sobre el frame de referencia)</Text>
          {[
            ['εxx', results.mapa_xx_url],
            ['εyy', results.mapa_yy_url],
            ['εxy', results.mapa_xy_url],
          ].map(([label, url]) => (
            <Image
              key={label}
              source={{ uri: storageUrl(url) }}
              style={styles.map}
              resizeMode="contain"
              accessibilityLabel={`Mapa de deformacion ${label}`}
            />
          ))}
        </>
      ) : null}

      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate(ROUTES.REPORTS, { projectId, projectName })}
      >
        <Text style={styles.buttonText}>Exportar y ver historial</Text>
      </TouchableOpacity>
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
  subtitle: {
    marginTop: spacing.xs,
    marginBottom: spacing.md,
    color: colors.mutedText,
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
  warningBox: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.warningSoft,
    borderWidth: 1,
    borderColor: colors.warningBorder,
    marginBottom: spacing.md,
  },
  warningTitle: {
    fontWeight: '700',
    color: colors.warning,
    marginBottom: spacing.xs,
  },
  warningText: {
    color: colors.warning,
    marginBottom: spacing.xs,
  },
  card: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  label: {
    color: colors.mutedText,
    marginBottom: spacing.sm,
  },
  value: {
    fontSize: typography.body,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.xs,
  },
  loading: {
    marginTop: spacing.sm,
    alignSelf: 'flex-start',
  },
  progressTrack: {
    height: 8,
    borderRadius: radii.sm,
    backgroundColor: colors.border,
    marginTop: spacing.sm,
    overflow: 'hidden',
  },
  progressFill: {
    height: 8,
    backgroundColor: colors.primary,
  },
  meta: {
    marginTop: spacing.sm,
    color: colors.mutedText,
    fontSize: typography.small,
  },
  cancelButton: {
    height: 44,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.dangerSoft,
    borderWidth: 1,
    borderColor: colors.dangerBorder,
    marginBottom: spacing.md,
  },
  cancelText: {
    color: colors.danger,
    fontWeight: '700',
  },
  rangeRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  input: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.md,
    paddingHorizontal: spacing.sm,
    backgroundColor: colors.background,
  },
  map: {
    width: '100%',
    aspectRatio: 1,
    marginBottom: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
  },
  button: {
    height: 48,
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
});
