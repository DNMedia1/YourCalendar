import React from "react";
import {
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import { ActionButton } from "../components/ActionButton.js";
import { NotificationBanner } from "../components/NotificationBanner.js";
import { colors } from "../theme/colors.js";
import { spacing } from "../theme/spacing.js";

export function AlphaBrowserScreen({ controller }) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.white} />
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.keyboardArea}
      >
        {controller.screen === "result" ? (
          <ResultScreen controller={controller} />
        ) : (
          <HomeScreen controller={controller} />
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function HomeScreen({ controller }) {
  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
      style={styles.page}
    >
      <View style={styles.header}>
        <Text style={styles.title}>MSBrowser Alpha</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Value</Text>
        <TextInput
          accessibilityLabel="Value"
          autoCapitalize="none"
          autoCorrect={false}
          multiline
          onChangeText={controller.handleValueChange}
          placeholder="https://"
          placeholderTextColor={colors.black}
          style={styles.input}
          value={controller.value}
        />
      </View>

      <NotificationBanner notification={controller.notification} />

      <View style={styles.actions}>
        <ActionButton
          disabled={controller.isBusy}
          label="Encrypt"
          onPress={controller.handleEncryptPress}
        />
        <ActionButton
          disabled={controller.isBusy}
          label="Decrypt"
          onPress={controller.handleDecryptPress}
          variant="secondary"
        />
      </View>
    </ScrollView>
  );
}

function ResultScreen({ controller }) {
  return (
    <ScrollView contentContainerStyle={styles.scrollContent} style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.title}>{controller.result?.title}</Text>
      </View>

      <View style={styles.resultBox}>
        <Text selectable style={styles.resultText}>
          {controller.result?.output}
        </Text>
      </View>

      <ActionButton label="Back" onPress={controller.handleBackPress} variant="secondary" />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: spacing.md
  },
  form: {
    gap: spacing.sm
  },
  header: {
    borderBottomColor: colors.green,
    borderBottomWidth: 2,
    paddingBottom: spacing.md
  },
  input: {
    backgroundColor: colors.white,
    borderColor: colors.green,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.black,
    fontSize: 16,
    minHeight: 132,
    padding: spacing.md,
    textAlignVertical: "top"
  },
  keyboardArea: {
    flex: 1
  },
  label: {
    color: colors.black,
    fontSize: 14,
    fontWeight: "700"
  },
  page: {
    backgroundColor: colors.white,
    flex: 1
  },
  resultBox: {
    backgroundColor: colors.greenLight,
    borderColor: colors.green,
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md
  },
  resultText: {
    color: colors.black,
    fontSize: 16,
    lineHeight: 24
  },
  safeArea: {
    backgroundColor: colors.white,
    flex: 1
  },
  scrollContent: {
    gap: spacing.lg,
    padding: spacing.lg
  },
  title: {
    color: colors.black,
    fontSize: 28,
    fontWeight: "800"
  }
});
