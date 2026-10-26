import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { logout } from '../../api/auth';
import { createProject, deleteProject, listProjects } from '../../api/projects';
import { ROUTES } from '../../navigation/routes';

const STATUS_LABELS = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  completed: 'Completado',
  failed: 'Fallo el analisis',
  revoked: 'Analisis cancelado',
};

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString();
  } catch {
    return '';
  }
}

export default function ProjectsScreen() {
  const navigation = useNavigation();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      setError(err.message || 'No fue posible cargar los proyectos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadProjects();
    }, [loadProjects])
  );

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await createProject(newName.trim());
      setNewName('');
      setShowCreate(false);
      await loadProjects();
    } catch (err) {
      Alert.alert('No fue posible crear el proyecto', err.message || '');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigation.reset({ index: 0, routes: [{ name: ROUTES.LOGIN }] });
  };

  const handleDelete = (project) => {
    Alert.alert('Eliminar proyecto', `¿Seguro que deseas eliminar "${project.name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Eliminar',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteProject(project.id);
            await loadProjects();
          } catch (err) {
            Alert.alert('No fue posible eliminar el proyecto', err.message || '');
          }
        },
      },
    ]);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Proyectos</Text>
        <TouchableOpacity style={styles.button} onPress={() => setShowCreate((prev) => !prev)}>
          <Text style={styles.buttonText}>{showCreate ? 'Cancelar' : 'Nuevo'}</Text>
        </TouchableOpacity>
      </View>

      {showCreate ? (
        <View style={styles.createBox}>
          <TextInput
            style={styles.input}
            placeholder="Nombre del proyecto"
            value={newName}
            onChangeText={setNewName}
            autoFocus
          />
          <TouchableOpacity
            style={[styles.button, styles.createButton]}
            onPress={handleCreate}
            disabled={creating || !newName.trim()}
          >
            {creating ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Crear proyecto</Text>}
          </TouchableOpacity>
        </View>
      ) : null}

      {loading ? (
        <ActivityIndicator style={styles.loading} color="#1f6feb" />
      ) : error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadProjects}>
            <Text style={styles.retryText}>Reintentar</Text>
          </TouchableOpacity>
        </View>
      ) : projects.length === 0 ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyText}>Aun no hay proyectos. Crea el primero para comenzar.</Text>
        </View>
      ) : (
        projects.map((project) => (
          <View key={project.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.projectName}>{project.name}</Text>
              <TouchableOpacity onPress={() => handleDelete(project)}>
                <Text style={styles.deleteText}>Eliminar</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.projectMeta}>
              {STATUS_LABELS[project.status] || project.status} · Creado {formatDate(project.created_at)}
            </Text>
            <View style={styles.cardActions}>
              <TouchableOpacity
                style={styles.cardAction}
                onPress={() =>
                  navigation.navigate(ROUTES.VIDEO_CAPTURE, { projectId: project.id, projectName: project.name })
                }
                accessibilityRole="button"
              >
                <Text style={styles.cardActionText}>Nuevo analisis</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.cardAction}
                onPress={() => navigation.navigate(ROUTES.REPORTS, { projectId: project.id, projectName: project.name })}
                accessibilityRole="button"
              >
                <Text style={styles.cardActionText}>Historial y reportes</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}

      <View style={styles.quickLinks}>
        <TouchableOpacity style={styles.quickLink} onPress={() => navigation.navigate(ROUTES.USER_MANUAL)}>
          <Text style={styles.quickLinkText}>Manual</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickLink} onPress={handleLogout} accessibilityRole="button">
          <Text style={styles.quickLinkText}>Cerrar sesion</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: '#f7f9fb',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#17202a',
  },
  button: {
    height: 40,
    borderRadius: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  createBox: {
    marginBottom: 18,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: '#d6dde5',
    borderRadius: 8,
    paddingHorizontal: 14,
    marginBottom: 10,
    backgroundColor: '#fff',
  },
  createButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 20,
  },
  loading: {
    marginTop: 24,
  },
  errorBox: {
    borderWidth: 1,
    borderColor: '#f5c6cb',
    backgroundColor: '#fdecea',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  errorText: {
    color: '#c0392b',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 10,
  },
  retryButton: {
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  retryText: {
    color: '#c0392b',
    fontWeight: '700',
  },
  emptyBox: {
    borderRadius: 8,
    padding: 24,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
    alignItems: 'center',
  },
  emptyText: {
    color: '#5d6d7e',
    textAlign: 'center',
  },
  card: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  projectName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
  },
  deleteText: {
    color: '#c0392b',
    fontWeight: '600',
    fontSize: 13,
  },
  projectMeta: {
    marginTop: 6,
    color: '#5d6d7e',
  },
  cardActions: {
    flexDirection: 'row',
    marginTop: 14,
  },
  cardAction: {
    flex: 1,
    marginRight: 8,
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#eef3fc',
  },
  cardActionText: {
    color: '#1f6feb',
    fontWeight: '700',
    fontSize: 13,
  },
  quickLinks: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 18,
  },
  quickLink: {
    flex: 1,
    marginHorizontal: 4,
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  quickLinkText: {
    color: '#5d6d7e',
    fontWeight: '600',
    fontSize: 13,
  },
});
