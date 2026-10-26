import { useNavigation, useRoute } from '@react-navigation/native';
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import * as DocumentPicker from 'expo-document-picker';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Image, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getFirstFrame, listCameras, openDevice, uploadVideo } from '../../api/devices';
import { ROUTES } from '../../navigation/routes';
import { colors, radii, spacing, touchTarget, typography } from '../../styles/theme';

const SOURCES = [
  { key: 'file', label: 'Subir video' },
  { key: 'phone', label: 'Grabar' },
  { key: 'camera', label: 'Camara PC' },
];

export default function VideoCaptureScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { projectId, projectName } = route.params || {};

  const [sourceType, setSourceType] = useState('file');
  const [cameras, setCameras] = useState([]);
  const [loadingCameras, setLoadingCameras] = useState(false);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [busyMessage, setBusyMessage] = useState('');
  const [recording, setRecording] = useState(false);
  const [source, setSource] = useState(null);
  const [frame, setFrame] = useState(null);
  const [error, setError] = useState('');
  const cameraRef = useRef(null);
  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [micPermission, requestMicPermission] = useMicrophonePermissions();

  useEffect(() => {
    if (sourceType !== 'camera' || cameras.length > 0) return;
    setLoadingCameras(true);
    listCameras()
      .then((list) => {
        setCameras(list);
        if (list.length > 0) setSelectedCameraId(list[0].id);
      })
      .catch((err) => setError(err.message || 'No fue posible listar las camaras.'))
      .finally(() => setLoadingCameras(false));
  }, [sourceType, cameras.length]);

  const run = async (message, task) => {
    setError('');
    setBusy(true);
    setBusyMessage(message);
    setSource(null);
    setFrame(null);
    try {
      const opened = await task();
      setSource(opened);
      setFrame(await getFirstFrame(opened.source_id));
    } catch (err) {
      setError(err.message || 'No fue posible abrir la fuente de video.');
    } finally {
      setBusy(false);
    }
  };

  const handlePickFile = async () => {
    const picked = await DocumentPicker.getDocumentAsync({ type: 'video/*', copyToCacheDirectory: true });
    if (picked.canceled || !picked.assets?.length) return;
    run('Subiendo video...', () => uploadVideo(picked.assets[0]));
  };

  const handleOpenServerCamera = () => {
    if (selectedCameraId === null) {
      setError('Selecciona una camara.');
      return;
    }
    run('Abriendo camara...', () => openDevice({ type: 'camera', source_id: selectedCameraId }));
  };

  const handleRecord = async () => {
    if (recording) {
      cameraRef.current?.stopRecording();
      return;
    }
    setError('');
    setRecording(true);
    try {
      const video = await cameraRef.current.recordAsync();
      setRecording(false);
      if (video?.uri) {
        run('Subiendo grabacion...', () =>
          uploadVideo({ uri: video.uri, name: 'grabacion.mp4', mimeType: 'video/mp4' })
        );
      }
    } catch (err) {
      setRecording(false);
      setError(err.message || 'No fue posible grabar el video.');
    }
  };

  const handleNext = () => {
    navigation.navigate(ROUTES.SETUP, {
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

  const renderPhone = () => {
    if (Platform.OS === 'web') {
      return <Text style={styles.muted}>La grabacion solo esta disponible en la app del celular. En el PC, sube el video.</Text>;
    }
    if (!cameraPermission?.granted || !micPermission?.granted) {
      return (
        <TouchableOpacity
          style={styles.button}
          onPress={async () => {
            await requestCameraPermission();
            await requestMicPermission();
          }}
        >
          <Text style={styles.buttonText}>Permitir camara y microfono</Text>
        </TouchableOpacity>
      );
    }
    return (
      <View>
        <Text style={styles.muted}>
          Usa tripode, sin zoom ni enfoque automatico, con la probeta paralela al sensor. No muevas el celular durante el
          ensayo: todo movimiento se mide como desplazamiento.
        </Text>
        <CameraView ref={cameraRef} style={styles.camera} mode="video" facing="back" />
        <TouchableOpacity
          style={[styles.button, recording && styles.stopButton]}
          onPress={handleRecord}
          disabled={busy}
          accessibilityRole="button"
        >
          <Text style={styles.buttonText}>{recording ? 'Detener y subir' : 'Iniciar grabacion'}</Text>
        </TouchableOpacity>
      </View>
    );
  };

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
        {SOURCES.map((s) => (
          <TouchableOpacity
            key={s.key}
            style={[styles.tab, sourceType === s.key && styles.tabActive]}
            onPress={() => setSourceType(s.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: sourceType === s.key }}
          >
            <Text style={[styles.tabText, sourceType === s.key && styles.tabTextActive]}>{s.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {sourceType === 'file' ? (
        <TouchableOpacity style={styles.button} onPress={handlePickFile} disabled={busy} accessibilityRole="button">
          <Text style={styles.buttonText}>Elegir archivo de video</Text>
        </TouchableOpacity>
      ) : null}

      {sourceType === 'phone' ? renderPhone() : null}

      {sourceType === 'camera' ? (
        <View>
          <Text style={styles.muted}>Camaras conectadas al servidor (Windows o Linux con V4L2; no disponible en Docker).</Text>
          {loadingCameras ? (
            <ActivityIndicator color={colors.primary} style={styles.loading} />
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
          )}
          <TouchableOpacity style={styles.button} onPress={handleOpenServerCamera} disabled={busy}>
            <Text style={styles.buttonText}>Abrir camara</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {busy ? (
        <View style={styles.busy}>
          <ActivityIndicator color={colors.primary} />
          <Text style={styles.muted}>{busyMessage}</Text>
        </View>
      ) : null}

      {frame ? (
        <View style={styles.previewBox}>
          <Text style={styles.previewLabel}>
            Vista previa · {source.width}x{source.height} · {source.fps.toFixed(1)} fps
            {source.duration_s ? ` · ${source.duration_s.toFixed(1)} s` : ''}
          </Text>
          <Image
            style={[styles.previewImage, { aspectRatio: source.width / source.height }]}
            source={{ uri: `data:${frame.mime_type};base64,${frame.image_base64}` }}
            resizeMode="contain"
          />
          <TouchableOpacity style={styles.nextButton} onPress={handleNext} accessibilityRole="button">
            <Text style={styles.buttonText}>Siguiente: configurar el ensayo</Text>
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
  tabs: {
    flexDirection: 'row',
    marginBottom: spacing.md,
  },
  tab: {
    flex: 1,
    height: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: {
    color: colors.mutedText,
    fontWeight: '600',
  },
  tabTextActive: {
    color: colors.onPrimary,
  },
  loading: {
    marginVertical: spacing.md,
  },
  muted: {
    color: colors.mutedText,
    marginBottom: spacing.md,
  },
  camera: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: radii.md,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  cameraOption: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.sm,
  },
  cameraOptionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySoft,
  },
  cameraName: {
    fontWeight: '700',
    color: colors.text,
  },
  cameraMeta: {
    marginTop: spacing.xs,
    color: colors.mutedText,
    fontSize: typography.small,
  },
  button: {
    height: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    marginTop: spacing.xs,
  },
  stopButton: {
    backgroundColor: colors.danger,
  },
  buttonText: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  busy: {
    marginTop: spacing.md,
    alignItems: 'center',
  },
  previewBox: {
    marginTop: spacing.lg,
  },
  previewLabel: {
    color: colors.mutedText,
    marginBottom: spacing.sm,
  },
  previewImage: {
    width: '100%',
    borderRadius: radii.md,
    backgroundColor: colors.frameBackground,
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
