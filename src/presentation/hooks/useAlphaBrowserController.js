import { useCallback, useEffect, useMemo, useState } from "react";
import { Linking } from "react-native";
import { DEFAULT_VALUE, NOTIFICATION_TYPES, WORKFLOW_TYPES } from "../../core/appDefaults.js";
import { AlphaBrowserWorkflow } from "../../core/workflow/AlphaBrowserWorkflow.js";
import { LogHandler } from "../../core/logging/LogHandler.js";
import { ValueValidator } from "../../core/validation/ValueValidator.js";

export function useAlphaBrowserController(options = {}) {
  const logHandler = useMemo(() => options.logHandler ?? new LogHandler(), [options.logHandler]);
  const workflow = useMemo(() => options.workflow ?? new AlphaBrowserWorkflow({ logHandler }), [
    logHandler,
    options.workflow
  ]);
  const validator = useMemo(() => options.validator ?? new ValueValidator(), [options.validator]);

  const [value, setValue] = useState(DEFAULT_VALUE);
  const [isBusy, setIsBusy] = useState(false);
  const [screen, setScreen] = useState("home");
  const [notification, setNotification] = useState(null);
  const [result, setResult] = useState(null);

  const showInfo = useCallback(message => {
    setNotification({
      type: NOTIFICATION_TYPES.info,
      message
    });
  }, []);

  const showWarning = useCallback(message => {
    setNotification({
      type: NOTIFICATION_TYPES.warning,
      message
    });
  }, []);

  const showError = useCallback(
    error => {
      logHandler.error("application error", error);
      setNotification({
        type: NOTIFICATION_TYPES.error,
        message: error.message ?? "Something went wrong."
      });
    },
    [logHandler]
  );

  useEffect(() => {
    let isMounted = true;

    loadInitialUrl(() => isMounted, workflow, setValue, showError);

    const subscription = Linking.addEventListener("url", event => {
      const incomingValue = workflow.resolveIncomingValue(event.url);

      if (incomingValue) {
        setValue(incomingValue);
        showInfo("Link loaded.");
      }
    });

    return () => {
      isMounted = false;
      subscription.remove();
    };
  }, [showError, showInfo, workflow]);

  const clearNotification = useCallback(() => {
    setNotification(null);
  }, []);

  const handleValueChange = useCallback(nextValue => {
    setValue(nextValue);
    setNotification(null);
  }, []);

  const handleEncryptPress = useCallback(() => {
    runTransform({
      title: "Encrypted value",
      type: WORKFLOW_TYPES.encrypt,
      value,
      validator,
      workflow,
      setIsBusy,
      setResult,
      setScreen,
      showWarning,
      showError
    });
  }, [showError, showWarning, validator, value, workflow]);

  const handleDecryptPress = useCallback(() => {
    runTransform({
      title: "Decrypted value",
      type: WORKFLOW_TYPES.decrypt,
      value,
      validator,
      workflow,
      setIsBusy,
      setResult,
      setScreen,
      showWarning,
      showError
    });
  }, [showError, showWarning, validator, value, workflow]);

  const handleBackPress = useCallback(() => {
    setScreen("home");
  }, []);

  return {
    clearNotification,
    handleBackPress,
    handleDecryptPress,
    handleEncryptPress,
    handleValueChange,
    isBusy,
    notification,
    result,
    screen,
    value
  };
}

async function loadInitialUrl(isMounted, workflow, setValue, showError) {
  try {
    const initialUrl = await Linking.getInitialURL();

    if (isMounted()) {
      setValue(workflow.resolveStartupValue(initialUrl));
    }
  } catch (error) {
    showError(error);
  }
}

async function runTransform(options) {
  const validation = options.validator.validate(options.value);

  if (!validation.isValid) {
    options.showWarning(validation.message);
    return;
  }

  options.setIsBusy(true);

  try {
    const output = await executeTransform(options.type, options.workflow, options.value);
    options.setResult({
      title: options.title,
      output
    });
    options.setScreen("result");
  } catch (error) {
    options.showError(error);
  } finally {
    options.setIsBusy(false);
  }
}

function executeTransform(type, workflow, value) {
  if (type === WORKFLOW_TYPES.encrypt) {
    return workflow.encryptValue(value);
  }

  return workflow.decryptValue(value);
}
