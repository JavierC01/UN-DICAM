import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { buildMesh, validateMesh } from '../../api/tracking';
import { startAnalysis } from '../../api/analysis';
import { ROUTES } from '../../navigation/routes';

const DEFAULT_PARAMS = { subset_size: '32', step_size: '8', search_range: '20' };

export default function MeshScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName, sourceId, frameWidth, frameHeight, frameBase64, frameMimeType } =
    route.params || {};

  const [points, setPoints] = useState([]);
  const [validation, setValidation] = useState(null);
  const [validating, setValidating] = useState(false);
  const [mesh, setMesh] = useState(null);
  const [building, setBuilding] = useState(false);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  const screenWidth = Dimensions.get('window').width;
  const displayWidth = screenWidth - 48;
  const displayHeight = frameWidth ? displayWidth * (frameHeight / frameWidth) : displayWidth;
  const scaleX = frameWidth ? displayWidth / frameWidth : 1;
  const scaleY = frameHeight ? displayHeight / frameHeight : 1;

  useEffect(() => {
    setMesh(null);
    if (points.length < 3 || !frameWidth || !frameHeight) {
      setValidation(null);
      return;
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

  const handleTap = (event) => {
    const { locationX, locationY } = event.nativeEvent;
    const x = Math.max(0, Math.min(frameWidth, locationX / scaleX));
    const y = Math.max(0, Math.min(frameHeight, locationY / scaleY));
    setPoints((prev) => [...prev, { x, y }]);
  };

  const handleUndo = () => setPoints((prev) => prev.slice(0, -1));
  const handleClear = () => setPoints([]);

  const handleBuildMesh = async () => {
    setError('');
    setBuilding(true);
    try {
      const result = await buildMesh({
        project_id: projectId,
        frame_width: frameWidth,
        frame_height: frameHeight,
        puntos: points,
      });
      setMesh(result);
    } catch (err) {
      setError(err.message || 'No fue posible construir la malla.');
    } finally {
      setBuilding(false);
    }
  };

  const handleStartAnalysis = async () => {
    setError('');
    const subsetSize = Number(params.subset_size);
    const stepSize = Number(params.step_size);
    const searchRange = Number(params.search_range);
    if (!subsetSize || !stepSize || !searchRange) {
      setError('Revisa los parametros de analisis, deben ser numeros mayores a cero.');
      return;
    }

    setStarting(true);
    try {
      const response = await startAnalysis({
        project_id: projectId,
        source_id: sourceId,
        subset_size: subsetSize,
        step_size: stepSize,
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

  if (!frameBase64) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>
          Vuelve a la pantalla de captura de video para obtener un frame antes de definir la malla.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Malla de rastreo</Text>
      <Text style={styles.subtitle}>Toca la imagen para marcar los puntos del poligono (minimo 3).</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <Pressable onPress={handleTap} style={[styles.imageWrapper, { width: displayWidth, height: displayHeight }]}>
        <Image
          style={{ width: displayWidth, height: displayHeight }}
          source={{ uri: `data:${frameMimeType || 'image/jpeg'};base64,${frameBase64}` }}
          resizeMode="contain"
        />
        {points.map((point, index) => (
          <View
            key={`point-${index}`}
            style={[styles.marker, { left: point.x * scaleX - 6, top: point.y * scaleY - 6 }]}
          >
            <Text style={styles.markerText}>{index + 1}</Text>
          </View>
        ))}
        {mesh?.nodos.map((node, index) => (
          <View
            key={`node-${index}`}
            style={[styles.nodeMarker, { left: node.x * scaleX - 4, top: node.y * scaleY - 4 }]}
          />
        ))}
      </Pressable>

      <View style={styles.pointActions}>
        <TouchableOpacity style={styles.smallButton} onPress={handleUndo} disabled={points.length === 0}>
          <Text style={styles.smallButtonText}>Deshacer punto</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.smallButton} onPress={handleClear} disabled={points.length === 0}>
          <Text style={styles.smallButtonText}>Limpiar</Text>
        </TouchableOpacity>
      </View>

      {validating ? (
        <ActivityIndicator color="#1f6feb" style={styles.loading} />
      ) : validation ? (
        <Text style={[styles.validationText, validation.valid ? styles.validText : styles.invalidText]}>
          {validation.message} (area: {Math.round(validation.area_px)} px²)
        </Text>
      ) : null}

      <TouchableOpacity
        style={styles.button}
        onPress={handleBuildMesh}
        disabled={!validation?.valid || building}
      >
        {building ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Construir malla</Text>}
      </TouchableOpacity>

      {mesh ? (
        <View style={styles.meshSummary}>
          <Text style={styles.meshSummaryText}>Malla construida: {mesh.nodos.length} nodos</Text>
        </View>
      ) : null}

      <View style={styles.paramsBox}>
        <Text style={styles.paramsTitle}>Parametros de analisis</Text>
        <View style={styles.paramsRow}>
          <View style={styles.paramField}>
            <Text style={styles.label}>Subset (px)</Text>
            <TextInput
              style={styles.input}
              keyboardType="number-pad"
              value={params.subset_size}
              onChangeText={(text) => setParams((prev) => ({ ...prev, subset_size: text }))}
            />
          </View>
          <View style={styles.paramField}>
            <Text style={styles.label}>Paso (px)</Text>
            <TextInput
              style={styles.input}
              keyboardType="number-pad"
              value={params.step_size}
              onChangeText={(text) => setParams((prev) => ({ ...prev, step_size: text }))}
            />
          </View>
          <View style={styles.paramField}>
            <Text style={styles.label}>Busqueda (px)</Text>
            <TextInput
              style={styles.input}
              keyboardType="number-pad"
              value={params.search_range}
              onChangeText={(text) => setParams((prev) => ({ ...prev, search_range: text }))}
            />
          </View>
        </View>
      </View>

      <TouchableOpacity style={styles.startButton} onPress={handleStartAnalysis} disabled={!mesh || starting}>
        {starting ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Iniciar analisis</Text>}
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
    fontSize: 26,
    fontWeight: '700',
    color: '#17202a',
  },
  subtitle: {
    marginTop: 4,
    marginBottom: 16,
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
  imageWrapper: {
    backgroundColor: '#1c2833',
    borderRadius: 8,
    overflow: 'hidden',
  },
  marker: {
    position: 'absolute',
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#1f6feb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  nodeMarker: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#2da44e',
  },
  pointActions: {
    flexDirection: 'row',
    marginTop: 12,
  },
  smallButton: {
    flex: 1,
    marginRight: 8,
    height: 38,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  smallButtonText: {
    color: '#5d6d7e',
    fontWeight: '600',
    fontSize: 13,
  },
  loading: {
    marginTop: 12,
  },
  validationText: {
    marginTop: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  validText: {
    color: '#2da44e',
  },
  invalidText: {
    color: '#c0392b',
  },
  button: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
    marginTop: 14,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  meshSummary: {
    marginTop: 12,
    alignItems: 'center',
  },
  meshSummaryText: {
    color: '#2da44e',
    fontWeight: '600',
  },
  paramsBox: {
    marginTop: 20,
    borderRadius: 8,
    padding: 16,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  paramsTitle: {
    fontWeight: '700',
    color: '#17202a',
    marginBottom: 10,
  },
  paramsRow: {
    flexDirection: 'row',
  },
  paramField: {
    flex: 1,
    marginRight: 8,
  },
  label: {
    color: '#5d6d7e',
    marginBottom: 6,
    fontSize: 13,
  },
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: '#d6dde5',
    borderRadius: 8,
    paddingHorizontal: 10,
    backgroundColor: '#f7f9fb',
  },
  startButton: {
    height: 52,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2da44e',
    marginTop: 20,
  },
});
