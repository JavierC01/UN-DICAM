import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export default function ReportsScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Reportes</Text>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Reporte tecnico</Text>
        <Text style={styles.cardText}>Prepara los resultados para exportacion.</Text>
        <TouchableOpacity style={styles.button}>
          <Text style={styles.buttonText}>Generar reporte</Text>
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
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 18,
    color: '#17202a',
  },
  card: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
  },
  cardText: {
    marginTop: 6,
    marginBottom: 16,
    color: '#5d6d7e',
  },
  button: {
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
});
