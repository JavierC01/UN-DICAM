import { useNavigation } from '@react-navigation/native';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { ROUTES } from '../../navigation/routes';

export default function ProjectsScreen() {
  const navigation = useNavigation();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Proyectos</Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate(ROUTES.VIDEO_CAPTURE)}>
          <Text style={styles.buttonText}>Nuevo</Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity style={styles.card} onPress={() => navigation.navigate(ROUTES.RESULTS)}>
        <Text style={styles.projectName}>Proyecto de ejemplo</Text>
        <Text style={styles.projectMeta}>Sin mediciones registradas</Text>
      </TouchableOpacity>
      <View style={styles.quickLinks}>
        <TouchableOpacity style={styles.quickLink} onPress={() => navigation.navigate(ROUTES.REPORTS)}>
          <Text style={styles.quickLinkText}>Reportes</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickLink} onPress={() => navigation.navigate(ROUTES.SETUP)}>
          <Text style={styles.quickLinkText}>Configuracion</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickLink} onPress={() => navigation.navigate(ROUTES.USER_MANUAL)}>
          <Text style={styles.quickLinkText}>Manual</Text>
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
  card: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  projectName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
  },
  projectMeta: {
    marginTop: 6,
    color: '#5d6d7e',
  },
  quickLinks: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 18,
  },
  quickLink: {
    flex: 1,
    marginHorizontal: 4,
    height: 40,
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
