import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { NOTIFICATION_TYPES } from "../../core/appDefaults.js";
import { colors } from "../theme/colors.js";
import { spacing } from "../theme/spacing.js";

export function NotificationBanner({ notification }) {
  if (!notification) {
    return null;
  }

  const style = getBannerStyle(notification.type);

  return (
    <View accessibilityRole="alert" style={[styles.container, style]}>
      <Text style={styles.message}>{notification.message}</Text>
    </View>
  );
}

function getBannerStyle(type) {
  if (type === NOTIFICATION_TYPES.error) {
    return styles.error;
  }

  if (type === NOTIFICATION_TYPES.warning) {
    return styles.warning;
  }

  return styles.info;
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md
  },
  error: {
    backgroundColor: colors.white,
    borderColor: colors.greenDark
  },
  info: {
    backgroundColor: colors.greenLight,
    borderColor: colors.green
  },
  message: {
    color: colors.black,
    fontSize: 14,
    lineHeight: 20
  },
  warning: {
    backgroundColor: colors.greenSoft,
    borderColor: colors.greenDark
  }
});
