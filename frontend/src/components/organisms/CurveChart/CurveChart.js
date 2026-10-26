import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { G, Line, Polyline, Text as SvgText } from 'react-native-svg';

import { colors, radii, spacing, typography } from '../../../styles/theme';
import { extent, formatTick, niceTicks, validPairs } from './scale';

const PADDING = { left: 56, right: 12, top: 12, bottom: 40 };
const HEIGHT = 240;

/**
 * Grafica x-y propia (react-native-svg). Los puntos con x o y nulos se omiten, nunca se dibujan como 0.
 * fit: { pendiente, intercepto, xMin, xMax } dibuja la recta del ajuste sobre su rango.
 */
export default function CurveChart({ title, x, y, xLabel, yLabel, fit }) {
  const [width, setWidth] = useState(0);
  const pairs = validPairs(x, y);
  const omitted = Math.max(x?.length || 0, y?.length || 0) - pairs.length;

  let body = null;
  if (width > 0 && pairs.length > 0) {
    const [xMin, xMax] = extent(pairs.map((p) => p[0]));
    const [yMin, yMax] = extent(pairs.map((p) => p[1]));
    const plotW = width - PADDING.left - PADDING.right;
    const plotH = HEIGHT - PADDING.top - PADDING.bottom;
    const sx = (v) => PADDING.left + ((v - xMin) / (xMax - xMin)) * plotW;
    const sy = (v) => PADDING.top + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

    body = (
      <Svg width={width} height={HEIGHT} accessibilityLabel={`Grafica ${title}`}>
        {niceTicks(yMin, yMax).map((t) => (
          <G key={`y-${t}`}>
            <Line x1={PADDING.left} x2={width - PADDING.right} y1={sy(t)} y2={sy(t)} stroke={colors.border} />
            <SvgText x={PADDING.left - 6} y={sy(t) + 4} fontSize={typography.caption - 2} fill={colors.mutedText} textAnchor="end">
              {formatTick(t)}
            </SvgText>
          </G>
        ))}
        {niceTicks(xMin, xMax).map((t) => (
          <G key={`x-${t}`}>
            <Line x1={sx(t)} x2={sx(t)} y1={PADDING.top} y2={PADDING.top + plotH} stroke={colors.border} />
            <SvgText x={sx(t)} y={PADDING.top + plotH + 14} fontSize={typography.caption - 2} fill={colors.mutedText} textAnchor="middle">
              {formatTick(t)}
            </SvgText>
          </G>
        ))}
        <Polyline
          points={pairs.map(([a, b]) => `${sx(a)},${sy(b)}`).join(' ')}
          fill="none"
          stroke={colors.primary}
          strokeWidth={2}
        />
        {fit ? (
          <Line
            x1={sx(fit.xMin)}
            y1={sy(fit.pendiente * fit.xMin + fit.intercepto)}
            x2={sx(fit.xMax)}
            y2={sy(fit.pendiente * fit.xMax + fit.intercepto)}
            stroke={colors.danger}
            strokeWidth={2}
            strokeDasharray="6,4"
          />
        ) : null}
        <SvgText x={PADDING.left + plotW / 2} y={HEIGHT - 6} fontSize={typography.caption} fill={colors.text} textAnchor="middle">
          {xLabel}
        </SvgText>
        <SvgText
          x={12}
          y={PADDING.top + plotH / 2}
          fontSize={typography.caption}
          fill={colors.text}
          textAnchor="middle"
          transform={`rotate(-90, 12, ${PADDING.top + plotH / 2})`}
        >
          {yLabel}
        </SvgText>
      </Svg>
    );
  }

  return (
    <View style={styles.card} onLayout={(e) => setWidth(e.nativeEvent.layout.width - spacing.md * 2)}>
      <Text style={styles.title}>{title}</Text>
      {pairs.length === 0 ? <Text style={styles.empty}>Sin datos validos para graficar.</Text> : body}
      {omitted > 0 ? <Text style={styles.note}>{omitted} puntos sin dato (nulos) no se grafican.</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radii.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  title: {
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  empty: {
    color: colors.mutedText,
  },
  note: {
    marginTop: spacing.xs,
    color: colors.mutedText,
    fontSize: typography.caption,
  },
});
