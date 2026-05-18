import { ScrollView, StyleSheet, Switch, Text, View } from 'react-native';

export default function SetupScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Configuracion</Text>
      <View style={styles.row}>
        <View>
          <Text style={styles.rowTitle}>Sincronizacion automatica</Text>
          <Text style={styles.rowText}>Enviar datos cuando haya conexion.</Text>
        </View>
        <Switch value={false} />
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
  row: {
    borderRadius: 8,
    padding: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e5eaf0',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  rowTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#17202a',
  },
  rowText: {
    marginTop: 4,
    color: '#5d6d7e',
  },
});
