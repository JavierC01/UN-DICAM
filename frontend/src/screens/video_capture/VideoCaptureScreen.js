import { useNavigation, useRoute } from '@react-navigation/native';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { getFirstFrame, listCameras, openDevice } from '../../api/devices';
import { ROUTES } from '../../navigation/routes';

export default function VideoCaptureScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName } = route.params || {};

  const [sourceType, setSourceType] = useState('camera');
  const [cameras, setCameras] = useState([]);
  const [loadingCameras, setLoadingCameras] = useState(true);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [filePath, setFilePath] = useState('');
  const [opening, setOpening] = useState(false);
  const [source, setSource] = useState(null);
  const [frame, setFrame] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const list = await listCameras();
        setCameras(list);
        if (list.length > 0) setSelectedCameraId(list[0].id);
      } catch (err) {
        setError(err.message || 'No fue posible listar las camaras.');
      } finally {
        setLoadingCameras(false);
      }
    })();
  }, []);

  const handleOpen = async () => {
    const sourceId = sourceType === 'camera' ? selectedCameraId : filePath.trim();
    if (sourceId === null || sourceId === undefined || sourceId === '') {
      setError(sourceType === 'camera' ? 'Selecciona una camara.' : 'Ingresa la ruta del archivo de video.');
      return;
    }

    setError('');
    setOpening(true);
    setSource(null);
    setFrame(null);
    try {
      const opened = await openDevice({ type: sourceType, source_id: sourceId });
      setSource(opened);
      const firstFrame = await getFirstFrame(opened.source_id);
      setFrame(firstFrame);
    } catch (err) {
      setError(err.message || 'No fue posible abrir la fuente de video.');
    } finally {
      setOpening(false);
    }
  };

  const handleNext = () => {
    navigation.navigate(ROUTES.MESH, {
      projectId,
      projectName,
      sourceId: source.source_id,
      frameWidth: source.width,
      frameHeight: source.height,
      frameBase64: frame.image_base64,
      frameMimeType: frame.mime_type,
    });
  };

  if (!projectId) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Selecciona un proyecto desde la lista para capturar video.</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Captura de video</Text>
      <Text style={styles.subtitle}>{projectName}</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, sourceType === 'camera' && styles.tabActive]}
          onPress={() => setSourceType('camera')}
        >
          <Text style={[styles.tabText, sourceType === 'camera' && styles.tabTextActive]}>Camara</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, sourceType === 'file' && styles.tabActive]}
          onPress={() => setSourceType('file')}
        >
          <Text style={[styles.tabText, sourceType === 'file' && styles.tabTextActive]}>Archivo</Text>
        </TouchableOpacity>
      </View>

      {sourceType === 'camera' ? (
        loadingCameras ? (
          <ActivityIndicator color="#1f6feb" style={styles.loading} />
        ) : cameras.length === 0 ? (
          <Text style={styles.muted}>No se detectaron camaras conectadas al servidor.</Text>
        ) : (
          cameras.map((camera) => (
            <TouchableOpacity
              key={camera.id}
              style={[styles.cameraOption, selectedCameraId === camera.id && styles.cameraOptionSelected]}
              onPress={() => setSelectedCameraId(camera.id)}
            >
              <Text style={styles.cameraName}>{camera.nombre}</Text>
              <Text style={styles.cameraMeta}>
                {camera.ancho}x{camera.alto} · {camera.fps.toFixed(0)} fps
              </Text>
            </TouchableOpacity>
          ))
        )
      ) : (
        <TextInput
          style={styles.input}
          placeholder="Ruta del archivo de video en el servidor"
          value={filePath}
          onChangeText={setFilePath}
          autoCapitalize="none"
        />
      )}

      <TouchableOpacity style={styles.button} onPress={handleOpen} disabled={opening}>
        {opening ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Abrir fuente</Text>}
      </TouchableOpacity>

      {frame ? (
        <View style={styles.previewBox}>
          <Text style={styles.previewLabel}>
            Vista previa · {source.width}x{source.height} · {source.fps.toFixed(1)} fps
          </Text>
          <Image
            style={[styles.previewImage, { aspectRatio: source.width / source.height }]}
            source={{ uri: `data:${frame.mime_type};base64,${frame.image_base64}` }}
            resizeMode="contain"
          />
          <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
            <Text style={styles.buttonText}>Siguiente: definir malla</Text>
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
  tabs: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  tabActive: {
    backgroundColor: '#1f6feb',
    borderColor: '#1f6feb',
  },
  tabText: {
    color: '#5d6d7e',
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#fff',
  },
  loading: {
    marginVertical: 12,
  },
  muted: {
    color: '#5d6d7e',
    marginBottom: 12,
  },
  cameraOption: {
    borderRadius: 8,
    padding: 14,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
    marginBottom: 8,
  },
  cameraOptionSelected: {
    borderColor: '#1f6feb',
    backgroundColor: '#eef3fc',
  },
  cameraName: {
    fontWeight: '700',
    color: '#17202a',
  },
  cameraMeta: {
    marginTop: 4,
    color: '#5d6d7e',
    fontSize: 13,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: '#d6dde5',
    borderRadius: 8,
    paddingHorizontal: 14,
    marginBottom: 12,
    backgroundColor: '#fff',
  },
  button: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
    marginTop: 4,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  previewBox: {
    marginTop: 20,
  },
  previewLabel: {
    color: '#5d6d7e',
    marginBottom: 8,
  },
  previewImage: {
    width: '100%',
    borderRadius: 8,
    backgroundColor: '#1c2833',
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
