import { ScrollView, StyleSheet, Text, View } from 'react-native';

export default function UserManualScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Manual de usuario</Text>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Primeros pasos</Text>
        <Text style={styles.sectionText}>
          Agrega aqui las instrucciones principales para operar la aplicacion.
        </Text>
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
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 18,
    color: '#17202a',
  },
  section: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
  },
  sectionText: {
    marginTop: 8,
    lineHeight: 22,
    color: '#5d6d7e',
  },
});
