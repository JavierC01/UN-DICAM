import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { startAnalysis } from '../../api/analysis';
import { listTestTypes } from '../../api/specimen';
import { buildMesh, setTestPoints, validateMesh } from '../../api/tracking';
import FrameAnnotator from '../../components/organisms/FrameAnnotator';
import { ROUTES } from '../../navigation/routes';
import { colors, radii, spacing, typography } from '../../styles/theme';

const DEFAULT_PARAMS = { subset_size: '32', search_range: '20' };
const DEFAULT_GRID = { filas: '6', columnas: '6' };
const MIN_GRID = 2;
const MAX_GRID = 20;

export default function MeshScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName, sourceId, frameWidth, frameHeight, frameBase64, frameMimeType, tipoEnsayo } =
    route.params || {};
  const imageUri = frameBase64 ? `data:${frameMimeType || 'image/jpeg'};base64,${frameBase64}` : null;

  const [points, setPoints] = useState([]);
  const [validation, setValidation] = useState(null);
  const [validating, setValidating] = useState(false);
  const [mesh, setMesh] = useState(null);
  const [building, setBuilding] = useState(false);
  const [grid, setGrid] = useState(DEFAULT_GRID);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [testType, setTestType] = useState(null);
  const [testPoints, setTestPointsState] = useState([]);
  const [testPointsSaved, setTestPointsSaved] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listTestTypes()
      .then((types) => setTestType(types.find((t) => t.tipo === (tipoEnsayo || 'traccion')) || null))
      .catch((err) => setError(err.message || 'No fue posible obtener el tipo de ensayo.'));
  }, [tipoEnsayo]);

  useEffect(() => {
    setMesh(null);
    if (points.length < 3 || !frameWidth || !frameHeight) {
      setValidation(null);
      return undefined;
    }
    let cancelled = false;
    setValidating(true);
    validateMesh({ project_id: projectId, frame_width: frameWidth, frame_height: frameHeight, puntos: points })
      .then((result) => {
        if (!cancelled) setValidation(result);
      })
      .catch((err) => {
        if (!cancelled) setValidation({ valid: false, area_px: 0, message: err.message });
      })
      .finally(() => {
        if (!cancelled) setValidating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [points, projectId, frameWidth, frameHeight]);

  const resetMesh = () => {
    setMesh(null);
    setTestPointsState([]);
    setTestPointsSaved(false);
  };

  const handleBuildMesh = async () => {
    setError('');
    const filas = Number(grid.filas);
    const columnas = Number(grid.columnas);
    const subsetSize = Number(params.subset_size);
    const fuera = (n) => !Number.isInteger(n) || n < MIN_GRID || n > MAX_GRID;
    if (fuera(filas) || fuera(columnas)) {
      setError(`Filas y columnas deben ser enteros entre ${MIN_GRID} y ${MAX_GRID}.`);
      return;
    }
    if (!Number.isInteger(subsetSize) || subsetSize < 5) {
      setError('El subset debe ser un entero de al menos 5 px.');
      return;
    }
    setBuilding(true);
    resetMesh();
    try {
      setMesh(
        await buildMesh({
          project_id: projectId,
          frame_width: frameWidth,
          frame_height: frameHeight,
          puntos: points,
          filas,
          columnas,
          subset_size: subsetSize,
        })
      );
    } catch (err) {
      setError(err.message || 'No fue posible construir la malla.');
    } finally {
      setBuilding(false);
    }
  };

  const handleSaveTestPoints = async () => {
    setError('');
    try {
      await setTestPoints(projectId, testPoints);
      setTestPointsSaved(true);
    } catch (err) {
      setError(err.message || 'No fue posible guardar los puntos del ensayo.');
    }
  };

  const handleStartAnalysis = async () => {
    setError('');
    const subsetSize = Number(params.subset_size);
    const searchRange = Number(params.search_range);
    if (!subsetSize || !searchRange) {
      setError('Revisa los parametros de analisis, deben ser numeros mayores a cero.');
      return;
    }

    setStarting(true);
    try {
      const response = await startAnalysis({
        project_id: projectId,
        source_id: sourceId,
        subset_size: subsetSize,
        search_range: searchRange,
        frame_inicio: 0,
      });
      navigation.navigate(ROUTES.RESULTS, { projectId, projectName, taskId: response.task_id });
    } catch (err) {
      setError(err.message || 'No fue posible iniciar el analisis.');
    } finally {
      setStarting(false);
    }
  };

  if (!imageUri) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>
          Vuelve a la pantalla de captura de video para obtener un frame antes de definir la malla.
        </Text>
      </View>
    );
  }

  const validCount = mesh ? mesh.validos.filter(Boolean).length : 0;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Malla de rastreo</Text>
      <Text style={styles.subtitle}>{projectName}</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <Text style={styles.section}>1. Region de interes</Text>
      <FrameAnnotator
        imageUri={imageUri}
        frameWidth={frameWidth}
        frameHeight={frameHeight}
        mode="polygon"
        points={points}
        onChange={setPoints}
        nodes={mesh?.nodos}
        validity={mesh?.validos}
        disabled={building}
        hint="Toca los vertices del contorno del objeto (minimo 3). La forma puede ser cualquiera: L, entalla, hueso de perro."
      />

      {validating ? (
        <ActivityIndicator color={colors.primary} style={styles.loading} />
      ) : validation ? (
        <Text style={[styles.validationText, validation.valid ? styles.validText : styles.invalidText]}>
          {validation.message} (area: {Math.round(validation.area_px)} px²)
        </Text>
      ) : null}

      <View style={styles.paramsBox}>
        <Text style={styles.paramsTitle}>Densidad de la malla y subset</Text>
        <View style={styles.paramsRow}>
          {[
            ['filas', 'Filas', grid, setGrid],
            ['columnas', 'Columnas', grid, setGrid],
            ['subset_size', 'Subset (px)', params, setParams],
          ].map(([key, label, state, setState]) => (
            <View key={key} style={styles.paramField}>
              <Text style={styles.label}>{label}</Text>
              <TextInput
                style={styles.input}
                keyboardType="number-pad"
                value={state[key]}
                accessibilityLabel={label}
                onChangeText={(text) => {
                  resetMesh();
                  setState((prev) => ({ ...prev, [key]: text }));
                }}
              />
            </View>
          ))}
        </View>
        <Text style={styles.label}>
          Solo son validos los nodos cuyo subset completo cae dentro de la forma; los demas se marcan en rojo y no se
          rastrean.
        </Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={handleBuildMesh} disabled={!validation?.valid || building}>
        {building ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.buttonText}>Construir malla</Text>}
      </TouchableOpacity>

      {mesh ? (
        <Text style={styles.meshSummaryText}>
          Malla {mesh.filas}×{mesh.columnas}: {validCount} nodos validos de {mesh.nodos.length}
        </Text>
      ) : null}

      {mesh && testType ? (
        <View>
          <Text style={styles.section}>2. Extensometro virtual ({testType.nombre})</Text>
          <FrameAnnotator
            imageUri={imageUri}
            frameWidth={frameWidth}
            frameHeight={frameHeight}
            mode="points"
            maxPoints={testType.n_puntos}
            points={testPoints}
            onChange={(next) => {
              setTestPointsState(next);
              setTestPointsSaved(false);
            }}
            nodes={mesh.nodos}
            validity={mesh.validos}
            referencePolygon={points}
            hint={`Marca ${testType.n_puntos} puntos dentro de la malla verde: ${testType.puntos}.`}
          />
          <TouchableOpacity
            style={styles.button}
            onPress={handleSaveTestPoints}
            disabled={testPoints.length !== testType.n_puntos || testPointsSaved}
          >
            <Text style={styles.buttonText}>{testPointsSaved ? 'Puntos guardados' : 'Guardar puntos del ensayo'}</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <View style={styles.paramsBox}>
        <Text style={styles.paramsTitle}>3. Parametros de analisis</Text>
        <Text style={styles.label}>Busqueda (px): desplazamiento maximo esperado entre el primer frame y cualquier otro.</Text>
        <TextInput
          style={styles.input}
          keyboardType="number-pad"
          value={params.search_range}
          onChangeText={(text) => setParams((prev) => ({ ...prev, search_range: text }))}
          accessibilityLabel="Rango de busqueda en px"
        />
        {mesh && !testPointsSaved ? (
          <Text style={styles.label}>
            Sin puntos del ensayo guardados, el analisis no tendra curva del ensayo ni propiedad (solo mapas y curvas
            generales).
          </Text>
        ) : null}
      </View>

      <TouchableOpacity style={styles.startButton} onPress={handleStartAnalysis} disabled={!mesh || starting}>
        {starting ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.buttonText}>Iniciar analisis</Text>}
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
  section: {
    fontSize: typography.subtitle,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
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
  loading: {
    marginTop: spacing.md,
  },
  validationText: {
    marginTop: spacing.md,
    fontWeight: '600',
    textAlign: 'center',
  },
  validText: {
    color: colors.success,
  },
  invalidText: {
    color: colors.danger,
  },
  button: {
    height: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    marginTop: spacing.md,
  },
  buttonText: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  meshSummaryText: {
    marginTop: spacing.md,
    color: colors.success,
    fontWeight: '600',
    textAlign: 'center',
  },
  paramsBox: {
    marginTop: spacing.lg,
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  paramsTitle: {
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  paramsRow: {
    flexDirection: 'row',
  },
  paramField: {
    flex: 1,
    marginRight: spacing.sm,
  },
  label: {
    color: colors.mutedText,
    marginTop: spacing.sm,
    marginBottom: spacing.xs,
    fontSize: typography.small,
  },
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.md,
    paddingHorizontal: spacing.sm,
    backgroundColor: colors.background,
  },
  startButton: {
    height: 52,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.success,
    marginTop: spacing.lg,
  },
});
