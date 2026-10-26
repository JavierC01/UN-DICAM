import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { colors, radii, spacing, touchTarget, typography } from '../../../styles/theme';

/** Seleccion de una opcion entre varias. options: [{ key, label }]. Envuelve en varias lineas si no caben. */
export default function SegmentedControl({ options, value, onChange, accessibilityLabel }) {
  return (
    <View style={styles.row} accessibilityRole="radiogroup" accessibilityLabel={accessibilityLabel}>
      {options.map((option) => {
        const selected = option.key === value;
        return (
          <TouchableOpacity
            key={option.key}
            style={[styles.option, selected && styles.selected]}
            onPress={() => onChange(option.key)}
            accessibilityRole="radio"
            accessibilityState={{ selected }}
            accessibilityLabel={option.label}
          >
            <Text style={[styles.text, selected && styles.selectedText]}>{option.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  option: {
    minHeight: touchTarget,
    paddingHorizontal: spacing.md,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  text: {
    color: colors.mutedText,
    fontWeight: '600',
    fontSize: typography.small,
  },
  selectedText: {
    color: colors.onPrimary,
  },
});
