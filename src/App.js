import React from "react";
import { AlphaBrowserScreen } from "./presentation/screens/AlphaBrowserScreen.js";
import { useAlphaBrowserController } from "./presentation/hooks/useAlphaBrowserController.js";

export default function App() {
  const controller = useAlphaBrowserController();

  return <AlphaBrowserScreen controller={controller} />;
}
