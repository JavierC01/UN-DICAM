import { useNavigation } from '@react-navigation/native';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { ROUTES } from '../../navigation/routes';

export default function VideoCaptureScreen() {
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <View style={styles.preview}>
        <Text style={styles.previewText}>Vista previa de video</Text>
      </View>
      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate(ROUTES.RESULTS)}>
        <Text style={styles.buttonText}>Iniciar captura</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#101820',
  },
  preview: {
    flex: 1,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1c2833',
  },
  previewText: {
    color: '#d6dde5',
    fontSize: 18,
  },
  button: {
    height: 52,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2da44e',
    marginTop: 16,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
});
