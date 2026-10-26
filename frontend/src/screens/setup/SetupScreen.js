import { useNavigation, useRoute } from '@react-navigation/native';
import * as DocumentPicker from 'expo-document-picker';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { NotFoundError } from '../../api/client';
import { getMachineLoad, importMachineFile } from '../../api/loads';
import { configureSpecimen, getSpecimen, listTestTypes } from '../../api/specimen';
import SegmentedControl from '../../components/molecules/SegmentedControl';
import FrameAnnotator, { lineLength, pointsFromRect, rectFromPoints } from '../../components/organisms/FrameAnnotator';
import { ROUTES } from '../../navigation/routes';
import { colors, radii, spacing, touchTarget, typography } from '../../styles/theme';

const FIELDS = [
  { key: 'long_calibracion_mm', label: 'Longitud real de la linea marcada (mm)' },
  { key: 'ancho_mm', label: 'Ancho de la seccion (mm)' },
  { key: 'espesor_mm', label: 'Espesor de la seccion (mm)' },
  { key: 'long_calibre_mm', label: 'Longitud de calibre (mm)' },
];

const LOAD_SOURCES = [
  { key: 'archivo', label: 'Archivo de la maquina' },
  { key: 'ocr', label: 'OCR del video' },
  { key: 'ninguna', label: 'Sin carga' },
];
const TIME_UNITS = ['s', 'ms', 'min'].map((u) => ({ key: u, label: u }));
const LOAD_UNITS = ['N', 'kN', 'kgf', 'tf', 'lbf'].map((u) => ({ key: u, label: u }));
const START_EVENTS = [
  { key: 'ninguno', label: 'Inicio del archivo = primer frame' },
  { key: 'umbral_carga', label: 'Cuando la carga supera un umbral' },
];

const toText = (value) => (value === null || value === undefined ? '' : String(value));

export default function SetupScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName, frameWidth, frameHeight, frameBase64, frameMimeType } = route.params || {};
  const imageUri = frameBase64 ? `data:${frameMimeType || 'image/jpeg'};base64,${frameBase64}` : null;

  const [values, setValues] = useState({ long_calibracion_mm: '', ancho_mm: '', espesor_mm: '', long_calibre_mm: '' });
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [manualPx, setManualPx] = useState('');
  const [testTypes, setTestTypes] = useState([]);
  const [testType, setTestType] = useState('traccion');
  const [testParams, setTestParams] = useState({ eje_carga: 'y', brazo_mm: '' });
  const [loadSource, setLoadSource] = useState('archivo');
  const [roiPoints, setRoiPoints] = useState([]);
  const [machineFile, setMachineFile] = useState(null);
  const [machineColumns, setMachineColumns] = useState([]);
  const [mapping, setMapping] = useState({
    columna_tiempo: '',
    columna_carga: '',
    unidad_tiempo: 's',
    unidad_carga: 'kN',
    offset_s: '0',
    evento_inicio: 'ninguno',
    umbral_n: '',
  });
  const [machineLoad, setMachineLoad] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        setTestTypes(await listTestTypes());
        const existing = await getSpecimen(projectId).catch((err) => {
          if (err instanceof NotFoundError) return null;
          throw err;
        });
        if (existing) {
          setSummary(existing);
          setValues({
            long_calibracion_mm: toText(existing.long_calibracion_mm),
            ancho_mm: toText(existing.ancho_mm),
            espesor_mm: toText(existing.espesor_mm),
            long_calibre_mm: toText(existing.long_calibre_mm),
          });
          setManualPx(toText(existing.long_calibracion_px));
          setTestType(existing.tipo_ensayo);
          setTestParams((prev) => ({ ...prev, ...existing.parametros_ensayo, brazo_mm: toText(existing.parametros_ensayo?.brazo_mm) }));
          setLoadSource(existing.fuente_carga);
          setRoiPoints(pointsFromRect(existing.roi_carga));
        }
        setMachineLoad(
          await getMachineLoad(projectId).catch((err) => {
            if (err instanceof NotFoundError) return null;
            throw err;
          })
        );
      } catch (err) {
        setError(err.message || 'No fue posible cargar la configuracion existente.');
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId]);

  const measuredPx = lineLength(calibrationPoints);
  const calibrationPx = measuredPx ?? Number(manualPx);
  const selectedTest = testTypes.find((t) => t.tipo === testType);

  const handlePickMachineFile = async () => {
    setError('');
    const picked = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'text/plain', 'text/comma-separated-values', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
      copyToCacheDirectory: true,
    });
    if (picked.canceled || !picked.assets?.length) return;
    const asset = picked.assets[0];
    setBusy(true);
    try {
      const response = await importMachineFile(projectId, asset);
      setMachineFile(asset);
      setMachineColumns(response.columnas);
      setMapping((prev) => ({
        ...prev,
        columna_tiempo: response.columnas[0] || '',
        columna_carga: response.columnas[1] || '',
      }));
    } catch (err) {
      setError(err.message || 'No fue posible leer el archivo de carga.');
    } finally {
      setBusy(false);
    }
  };

  const handleImportMachineFile = async () => {
    setError('');
    if (mapping.evento_inicio === 'umbral_carga' && !(Number(mapping.umbral_n) > 0)) {
      setError('Ingresa el umbral de carga (N) para sincronizar el inicio.');
      return;
    }
    setBusy(true);
    try {
      setMachineLoad(await importMachineFile(projectId, machineFile, mapping));
      setMachineFile(null);
      setMachineColumns([]);
    } catch (err) {
      setError(err.message || 'No fue posible importar el archivo de carga.');
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    setError('');
    if (!(calibrationPx > 0)) {
      setError('Marca sobre el frame una distancia conocida (o escribe su longitud en px).');
      return;
    }
    const parsed = {};
    for (const field of FIELDS) {
      const num = Number(values[field.key]);
      if (!values[field.key] || Number.isNaN(num) || num <= 0) {
        setError(`Ingresa un valor valido para "${field.label}".`);
        return;
      }
      parsed[field.key] = num;
    }
    const parametros = {};
    if (testType === 'cortante') parametros.eje_carga = testParams.eje_carga;
    if (testType === 'portico') {
      const brazo = Number(testParams.brazo_mm);
      if (!(brazo > 0)) {
        setError('Ingresa el brazo de la carga al nudo (mm) para el ensayo de portico.');
        return;
      }
      parametros.brazo_mm = brazo;
    }
    const roi = loadSource === 'ocr' ? rectFromPoints(roiPoints) : null;
    if (loadSource === 'ocr' && !roi) {
      setError('Dibuja sobre el frame el rectangulo donde se ve el valor de la carga.');
      return;
    }
    if (loadSource === 'archivo' && !machineLoad) {
      setError('Importa el archivo de carga de la maquina antes de guardar.');
      return;
    }

    setBusy(true);
    try {
      const response = await configureSpecimen({
        project_id: projectId,
        long_calibracion_px: calibrationPx,
        ...parsed,
        tipo_ensayo: testType,
        parametros_ensayo: parametros,
        fuente_carga: loadSource,
        roi_carga: roi,
      });
      setSummary(response);
    } catch (err) {
      setError(err.message || 'No fue posible guardar la configuracion.');
    } finally {
      setBusy(false);
    }
  };

  if (!projectId || !imageUri) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>
          Abre primero la fuente de video desde Captura: la calibracion y la region de carga se marcan sobre el frame.
        </Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Configuracion del ensayo</Text>
      <Text style={styles.subtitle}>{projectName}</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <Text style={styles.section}>1. Calibracion px ↔ mm</Text>
      <FrameAnnotator
        imageUri={imageUri}
        frameWidth={frameWidth}
        frameHeight={frameHeight}
        mode="line"
        points={calibrationPoints}
        onChange={setCalibrationPoints}
        hint="Toca los dos extremos de una distancia conocida (regla, marcas o largo de la probeta)."
      />
      {measuredPx ? (
        <Text style={styles.info}>Distancia marcada: {measuredPx.toFixed(1)} px</Text>
      ) : (
        <View style={styles.field}>
          <Text style={styles.label}>O escribe la distancia en px</Text>
          <TextInput style={styles.input} keyboardType="decimal-pad" value={manualPx} onChangeText={setManualPx} />
        </View>
      )}

      {FIELDS.map((field) => (
        <View key={field.key} style={styles.field}>
          <Text style={styles.label}>{field.label}</Text>
          <TextInput
            style={styles.input}
            keyboardType="decimal-pad"
            value={values[field.key]}
            onChangeText={(text) => setValues((prev) => ({ ...prev, [field.key]: text }))}
            accessibilityLabel={field.label}
          />
        </View>
      ))}

      <Text style={styles.section}>2. Tipo de ensayo</Text>
      <SegmentedControl
        options={testTypes.map((t) => ({ key: t.tipo, label: t.nombre }))}
        value={testType}
        onChange={setTestType}
        accessibilityLabel="Tipo de ensayo"
      />
      {selectedTest ? (
        <Text style={styles.info}>
          Curva: {selectedTest.respuesta.nombre} [{selectedTest.respuesta.unidad}] vs {selectedTest.medida.nombre} [
          {selectedTest.medida.unidad}] → {selectedTest.propiedad.nombre}. En la malla marcaras {selectedTest.n_puntos} puntos:{' '}
          {selectedTest.puntos}.
        </Text>
      ) : null}
      {testType === 'cortante' ? (
        <View style={styles.field}>
          <Text style={styles.label}>Direccion de la carga en la imagen</Text>
          <SegmentedControl
            options={[
              { key: 'y', label: 'Vertical (y)' },
              { key: 'x', label: 'Horizontal (x)' },
            ]}
            value={testParams.eje_carga}
            onChange={(eje) => setTestParams((prev) => ({ ...prev, eje_carga: eje }))}
          />
        </View>
      ) : null}
      {testType === 'portico' ? (
        <View style={styles.field}>
          <Text style={styles.label}>Brazo de la carga al nudo (mm)</Text>
          <TextInput
            style={styles.input}
            keyboardType="decimal-pad"
            value={testParams.brazo_mm}
            onChangeText={(text) => setTestParams((prev) => ({ ...prev, brazo_mm: text }))}
          />
        </View>
      ) : null}

      <Text style={styles.section}>3. Fuente de la carga</Text>
      <SegmentedControl options={LOAD_SOURCES} value={loadSource} onChange={setLoadSource} accessibilityLabel="Fuente de carga" />

      {loadSource === 'ocr' ? (
        <View style={styles.block}>
          <FrameAnnotator
            imageUri={imageUri}
            frameWidth={frameWidth}
            frameHeight={frameHeight}
            mode="rect"
            points={roiPoints}
            onChange={setRoiPoints}
            hint="Dibuja el rectangulo donde la pantalla de la maquina muestra la carga (en N). Toca dos esquinas opuestas."
          />
          <Text style={styles.info}>Los frames donde el OCR no lea un numero se descartan y se reportan.</Text>
        </View>
      ) : null}

      {loadSource === 'archivo' ? (
        <View style={styles.block}>
          {machineLoad ? (
            <View style={styles.summaryBox}>
              <Text style={styles.summaryTitle}>Archivo importado: {machineLoad.nombre_archivo}</Text>
              <Text style={styles.summaryText}>
                {machineLoad.n_puntos} puntos · {machineLoad.duracion_s.toFixed(1)} s · carga max{' '}
                {machineLoad.carga_max_n.toFixed(1)} N · {machineLoad.filas_descartadas} filas descartadas
              </Text>
            </View>
          ) : null}
          <TouchableOpacity style={styles.secondaryButton} onPress={handlePickMachineFile} disabled={busy}>
            <Text style={styles.secondaryButtonText}>
              {machineLoad ? 'Reemplazar archivo (CSV/XLSX)' : 'Elegir archivo de la maquina (CSV/XLSX)'}
            </Text>
          </TouchableOpacity>

          {machineColumns.length > 0 ? (
            <View style={styles.summaryBox}>
              <Text style={styles.label}>Columna de tiempo</Text>
              <SegmentedControl
                options={machineColumns.map((c) => ({ key: c, label: c }))}
                value={mapping.columna_tiempo}
                onChange={(c) => setMapping((prev) => ({ ...prev, columna_tiempo: c }))}
              />
              <Text style={styles.label}>Unidad de tiempo</Text>
              <SegmentedControl
                options={TIME_UNITS}
                value={mapping.unidad_tiempo}
                onChange={(u) => setMapping((prev) => ({ ...prev, unidad_tiempo: u }))}
              />
              <Text style={styles.label}>Columna de carga</Text>
              <SegmentedControl
                options={machineColumns.map((c) => ({ key: c, label: c }))}
                value={mapping.columna_carga}
                onChange={(c) => setMapping((prev) => ({ ...prev, columna_carga: c }))}
              />
              <Text style={styles.label}>Unidad de carga</Text>
              <SegmentedControl
                options={LOAD_UNITS}
                value={mapping.unidad_carga}
                onChange={(u) => setMapping((prev) => ({ ...prev, unidad_carga: u }))}
              />
              <Text style={styles.label}>Sincronizacion con el video</Text>
              <SegmentedControl
                options={START_EVENTS}
                value={mapping.evento_inicio}
                onChange={(e) => setMapping((prev) => ({ ...prev, evento_inicio: e }))}
              />
              {mapping.evento_inicio === 'umbral_carga' ? (
                <TextInput
                  style={[styles.input, styles.spaced]}
                  keyboardType="decimal-pad"
                  placeholder="Umbral de carga (N)"
                  value={mapping.umbral_n}
                  onChangeText={(t) => setMapping((prev) => ({ ...prev, umbral_n: t }))}
                />
              ) : null}
              <Text style={styles.label}>Desfase adicional (s; positivo si la maquina empezo antes que el video)</Text>
              <TextInput
                style={styles.input}
                keyboardType="numbers-and-punctuation"
                value={mapping.offset_s}
                onChangeText={(t) => setMapping((prev) => ({ ...prev, offset_s: t }))}
              />
              <TouchableOpacity style={styles.button} onPress={handleImportMachineFile} disabled={busy}>
                <Text style={styles.buttonText}>Importar carga</Text>
              </TouchableOpacity>
            </View>
          ) : null}
        </View>
      ) : null}

      {loadSource === 'ninguna' ? (
        <Text style={styles.info}>Sin carga, el analisis entrega desplazamientos y deformaciones; carga y esfuerzo quedan vacios.</Text>
      ) : null}

      <TouchableOpacity style={styles.button} onPress={handleSave} disabled={busy}>
        {busy ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.buttonText}>Guardar configuracion</Text>}
      </TouchableOpacity>

      {summary ? (
        <View style={styles.summaryBox}>
          <Text style={styles.summaryTitle}>Configuracion guardada</Text>
          <Text style={styles.summaryText}>px/mm: {summary.px_por_mm.toFixed(4)}</Text>
          <Text style={styles.summaryText}>mm/px: {summary.mm_por_px.toFixed(4)}</Text>
          <Text style={styles.summaryText}>Area: {summary.area_mm2.toFixed(2)} mm²</Text>
          <Text style={styles.summaryText}>
            Ensayo: {summary.tipo_ensayo} · carga: {summary.fuente_carga}
          </Text>
          <TouchableOpacity
            style={styles.nextButton}
            onPress={() =>
              navigation.navigate(ROUTES.MESH, { ...route.params, tipoEnsayo: summary.tipo_ensayo })
            }
          >
            <Text style={styles.buttonText}>Continuar a la malla</Text>
          </TouchableOpacity>
        </View>
      ) : null}
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
  section: {
    fontSize: typography.subtitle,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  block: {
    marginTop: spacing.md,
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
  info: {
    color: colors.mutedText,
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  field: {
    marginTop: spacing.md,
  },
  label: {
    color: colors.mutedText,
    marginTop: spacing.sm,
    marginBottom: spacing.xs,
    fontWeight: '600',
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
  },
  spaced: {
    marginTop: spacing.sm,
  },
  button: {
    height: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    marginTop: spacing.lg,
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
    marginTop: spacing.sm,
  },
  secondaryButtonText: {
    color: colors.primary,
    fontWeight: '700',
  },
  summaryBox: {
    marginTop: spacing.md,
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  summaryTitle: {
    fontSize: typography.body,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  summaryText: {
    color: colors.mutedText,
    marginBottom: spacing.xs,
  },
  nextButton: {
    height: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.success,
    marginTop: spacing.md,
  },
});
