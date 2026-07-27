import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { colors } from "../theme/colors.js";
import { spacing } from "../theme/spacing.js";

export function ActionButton({ label, onPress, variant = "primary", disabled = false }) {
  const buttonStyle = variant === "secondary" ? styles.secondaryButton : styles.primaryButton;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        buttonStyle,
        disabled && styles.disabledButton,
        pressed && !disabled && styles.pressedButton
      ]}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    borderRadius: 8,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  buttonText: {
    color: colors.black,
    fontSize: 16,
    fontWeight: "700"
  },
  disabledButton: {
    opacity: 0.6
  },
  pressedButton: {
    opacity: 0.84
  },
  primaryButton: {
    backgroundColor: colors.green,
    borderColor: colors.greenDark
  },
  secondaryButton: {
    backgroundColor: colors.white,
    borderColor: colors.green
  }
});
