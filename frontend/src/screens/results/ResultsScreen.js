import { useNavigation } from '@react-navigation/native';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { ROUTES } from '../../navigation/routes';

export default function ResultsScreen() {
  const navigation = useNavigation();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Resultados</Text>
      <View style={styles.card}>
        <Text style={styles.label}>Estado del analisis</Text>
        <Text style={styles.value}>Pendiente de datos</Text>
      </View>
      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate(ROUTES.REPORTS)}>
        <Text style={styles.buttonText}>Ver reportes</Text>
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
  button: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f6feb',
    marginTop: 16,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
});
