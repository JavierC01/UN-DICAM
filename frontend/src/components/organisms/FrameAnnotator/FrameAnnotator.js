import { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Svg, { Circle, Line, Polygon, Rect, Text as SvgText } from 'react-native-svg';

import { colors, radii, spacing, touchTarget, typography } from '../../../styles/theme';
import { addPoint, rectFromPoints } from './geometry';

const MODE_HINTS = {
  line: 'Toca los dos extremos de la distancia conocida.',
  rect: 'Toca dos esquinas opuestas del rectangulo.',
  polygon: 'Toca para agregar vertices (minimo 3).',
  points: 'Toca para marcar los puntos en orden.',
};

/**
 * Muestra un frame y permite marcar sobre el. Recibe y devuelve coordenadas en pixeles del frame original,
 * sin importar el tamano con que se dibuje.
 *
 * mode: 'line' (2 puntos), 'rect' (2 esquinas), 'polygon' (vertices) o 'points' (hasta maxPoints).
 * nodes/validity: nodos de la malla a dibujar (verde valido, rojo invalido). referencePolygon: contorno de guia.
 */
export default function FrameAnnotator({
  imageUri,
  frameWidth,
  frameHeight,
  mode = 'polygon',
  points = [],
  onChange,
  maxPoints,
  nodes = [],
  validity = [],
  referencePolygon = [],
  hint,
  disabled = false,
}) {
  const [displayWidth, setDisplayWidth] = useState(0);
  const scale = frameWidth ? displayWidth / frameWidth : 1;
  const displayHeight = frameHeight * scale;
  const toScreen = (p) => `${p.x * scale},${p.y * scale}`;

  const handlePress = (event) => {
    if (disabled || !scale) return;
    const { locationX, locationY } = event.nativeEvent;
    const x = Math.max(0, Math.min(frameWidth, locationX / scale));
    const y = Math.max(0, Math.min(frameHeight, locationY / scale));
    onChange(addPoint(points, { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 }, mode, maxPoints));
  };

  const rect = mode === 'rect' ? rectFromPoints(points) : null;

  return (
    <View>
      <Text style={styles.hint}>{hint || MODE_HINTS[mode]}</Text>
      <View style={styles.wrapper} onLayout={(e) => setDisplayWidth(e.nativeEvent.layout.width)}>
        {displayWidth > 0 ? (
          <Pressable
            onPress={handlePress}
            style={{ width: displayWidth, height: displayHeight }}
            accessibilityRole="imagebutton"
            accessibilityLabel={`Frame para marcar: ${MODE_HINTS[mode]}`}
          >
            <Image style={{ width: displayWidth, height: displayHeight }} source={{ uri: imageUri }} resizeMode="stretch" />
            <Svg style={StyleSheet.absoluteFill} width={displayWidth} height={displayHeight} pointerEvents="none">
              {referencePolygon.length >= 3 ? (
                <Polygon
                  points={referencePolygon.map(toScreen).join(' ')}
                  fill="none"
                  stroke={colors.primary}
                  strokeWidth={1.5}
                  strokeDasharray="6,4"
                />
              ) : null}
              {nodes.map((node, i) => (
                <Circle
                  key={`n-${i}`}
                  cx={node.x * scale}
                  cy={node.y * scale}
                  r={3}
                  fill={validity[i] === false ? colors.invalidNode : colors.success}
                />
              ))}
              {mode === 'polygon' && points.length >= 3 ? (
                <Polygon
                  points={points.map(toScreen).join(' ')}
                  fill={colors.annotation}
                  fillOpacity={0.15}
                  stroke={colors.annotation}
                  strokeWidth={2}
                />
              ) : null}
              {(mode === 'line' || mode === 'polygon') && points.length === 2 ? (
                <Line
                  x1={points[0].x * scale}
                  y1={points[0].y * scale}
                  x2={points[1].x * scale}
                  y2={points[1].y * scale}
                  stroke={colors.annotation}
                  strokeWidth={2}
                />
              ) : null}
              {rect ? (
                <Rect
                  x={rect.x * scale}
                  y={rect.y * scale}
                  width={rect.width * scale}
                  height={rect.height * scale}
                  fill={colors.annotation}
                  fillOpacity={0.2}
                  stroke={colors.annotation}
                  strokeWidth={2}
                />
              ) : null}
              {points.map((p, i) => (
                <Circle key={`p-${i}`} cx={p.x * scale} cy={p.y * scale} r={9} fill={colors.primary} />
              ))}
              {points.map((p, i) => (
                <SvgText
                  key={`t-${i}`}
                  x={p.x * scale}
                  y={p.y * scale + 4}
                  fontSize={typography.caption}
                  fontWeight="bold"
                  fill={colors.onPrimary}
                  textAnchor="middle"
                >
                  {i + 1}
                </SvgText>
              ))}
            </Svg>
          </Pressable>
        ) : null}
      </View>
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.action}
          onPress={() => onChange(points.slice(0, -1))}
          disabled={disabled || points.length === 0}
          accessibilityRole="button"
          accessibilityLabel="Deshacer el ultimo punto"
        >
          <Text style={styles.actionText}>Deshacer</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.action}
          onPress={() => onChange([])}
          disabled={disabled || points.length === 0}
          accessibilityRole="button"
          accessibilityLabel="Borrar todos los puntos"
        >
          <Text style={styles.actionText}>Limpiar</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  hint: {
    color: colors.mutedText,
    fontSize: typography.small,
    marginBottom: spacing.sm,
  },
  wrapper: {
    width: '100%',
    backgroundColor: colors.frameBackground,
    borderRadius: radii.md,
    overflow: 'hidden',
  },
  actions: {
    flexDirection: 'row',
    marginTop: spacing.sm,
    gap: spacing.sm,
  },
  action: {
    flex: 1,
    minHeight: touchTarget,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionText: {
    color: colors.mutedText,
    fontWeight: '600',
    fontSize: typography.small,
  },
});
