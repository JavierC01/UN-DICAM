import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export default function ProjectsScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Proyectos</Text>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Nuevo</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.card}>
        <Text style={styles.projectName}>Proyecto de ejemplo</Text>
        <Text style={styles.projectMeta}>Sin mediciones registradas</Text>
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
});
