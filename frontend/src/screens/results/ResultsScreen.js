import { ScrollView, StyleSheet, Text, View } from 'react-native';

export default function ResultsScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Resultados</Text>
      <View style={styles.card}>
        <Text style={styles.label}>Estado del analisis</Text>
        <Text style={styles.value}>Pendiente de datos</Text>
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
  label: {
    color: '#5d6d7e',
    marginBottom: 6,
  },
  value: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17202a',
  },
});
