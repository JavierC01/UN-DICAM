import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '../../styles/theme';

const SECTIONS = [
  {
    title: 'Que hace UN-DICAM',
    text:
      'Correlacion digital de imagenes (DIC) 2D con una sola camara: rastrea una malla de puntos sobre el video del ' +
      'ensayo y entrega desplazamientos, mapas de deformacion, curvas carga-desplazamiento y esfuerzo-deformacion, y la ' +
      'propiedad del ensayo (modulo de elasticidad, rigidez, modulo de deslizamiento o rigidez rotacional).',
  },
  {
    title: '1. Preparar la probeta y la camara',
    text:
      'Pinta un patron de puntos (speckle) aleatorio, de alto contraste y sin brillos sobre la cara visible. Pon la ' +
      'camara en tripode, perpendicular a esa cara, sin zoom ni enfoque automatico, con iluminacion constante. Incluye en ' +
      'el cuadro una distancia conocida (regla o marcas) para calibrar. Limitacion 2D: el objeto debe moverse en el plano ' +
      'de la imagen; cualquier movimiento hacia o desde la camara se mide como deformacion falsa.',
  },
  {
    title: '2. Proyecto y video',
    text:
      'Crea un proyecto y toca "Nuevo analisis". Sube el video del ensayo, grabalo con el celular (sin mover el telefono) o ' +
      'usa una camara conectada al servidor. El primer frame es la referencia: debe mostrar la probeta sin carga.',
  },
  {
    title: '3. Configurar el ensayo',
    text:
      'Calibracion: toca los dos extremos de la distancia conocida y escribe su longitud real en mm. Ingresa ancho y espesor ' +
      'de la seccion (el area se usa para el esfuerzo). Elige el tipo de ensayo: traccion, compresion, flexion, cortante / ' +
      'conexion o momento en portico (este ultimo pide el brazo de la carga al nudo).',
  },
  {
    title: '4. Carga',
    text:
      'Archivo de la maquina (recomendado): sube el CSV o XLSX exportado, elige las columnas de tiempo y carga con sus ' +
      'unidades y la sincronizacion (inicio del archivo = primer frame, o el instante en que la carga supera un umbral, mas ' +
      'un desfase en segundos). OCR: dibuja el rectangulo donde la pantalla de la maquina muestra la carga en N. Si una ' +
      'lectura falla o un frame cae fuera del registro, ese punto queda sin carga y se reporta; nunca se reemplaza por cero.',
  },
  {
    title: '5. Malla y extensometro virtual',
    text:
      'Marca el contorno del objeto con los vertices que necesites: la forma puede ser no rectangular. Elige filas, ' +
      'columnas y el tamano del subset. Solo son validos (verde) los nodos cuyo subset completo cae dentro de la forma; los ' +
      'rojos no se rastrean. Luego marca los puntos del ensayo: traccion y compresion, los extremos de la longitud de ' +
      'calibre; flexion, apoyo izquierdo, centro y apoyo derecho; cortante, un punto en cada elemento de la conexion; ' +
      'portico, dos puntos sobre el elemento que gira.',
  },
  {
    title: '6. Parametros',
    text:
      'Subset: lado en px de la ventana que se correlaciona; debe contener varios puntos del speckle (tipicamente 21 a 41). ' +
      'Busqueda: desplazamiento maximo esperado, en px, entre el primer frame y cualquier otro. Si el analisis pierde nodos, ' +
      'aumenta la busqueda; si es muy lento, reducela o usa menos nodos.',
  },
  {
    title: '7. Resultados',
    text:
      'Revisa primero las advertencias. Los mapas muestran la deformacion del ultimo frame sobre la imagen de referencia, ' +
      'por triangulos. Para la propiedad, elige el rango del ajuste lineal segun la norma que aplique a tu material (por ' +
      'ejemplo un rango de deformacion, o 10 %-40 % de la carga maxima): la app reporta la pendiente, el R² y el rango usado ' +
      'y nunca lo elige por ti.',
  },
  {
    title: '8. Exportar',
    text:
      'En Reportes elige el analisis y descarga el CSV (datos por frame), el PDF (reporte tecnico) o el JPG (curvas y mapas). ' +
      'Todos incluyen los metadatos de reproducibilidad: parametros, calibracion, metodo de carga, hash del video y version ' +
      'del software.',
  },
  {
    title: 'Antes de usar los resultados',
    text:
      'UN-DICAM esta en desarrollo. Contrasta los resultados con un extensometro, LVDT o galga antes de usarlos para ' +
      'decisiones de ingenieria.',
  },
];

export default function UserManualScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Manual de usuario</Text>
      {SECTIONS.map((section) => (
        <View key={section.title} style={styles.section}>
          <Text style={styles.sectionTitle} accessibilityRole="header">
            {section.title}
          </Text>
          <Text style={styles.sectionText}>{section.text}</Text>
        </View>
      ))}
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
    marginBottom: spacing.md,
    color: colors.text,
  },
  section: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: typography.subtitle,
    fontWeight: '700',
    color: colors.text,
  },
  sectionText: {
    marginTop: spacing.sm,
    lineHeight: 22,
    color: colors.mutedText,
  },
});
