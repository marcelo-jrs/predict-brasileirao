"use client";

import { createContext, useCallback, useContext, useSyncExternalStore } from "react";

import type { ModelId } from "@/lib/types";

const STORAGE_KEY = "brasileirao-model";

// The chosen model lives in localStorage (an "external store"), so it persists across pages and visits.
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

const readSaved = () => window.localStorage.getItem(STORAGE_KEY);
const readOnServer = () => null;

interface ModelState {
  model: ModelId;
  models: ModelId[];
  setModel: (model: ModelId) => void;
}

const ModelContext = createContext<ModelState | null>(null);

export function ModelProvider({
  models,
  defaultModel,
  children,
}: {
  models: ModelId[];
  defaultModel: ModelId;
  children: React.ReactNode;
}) {
  const saved = useSyncExternalStore(subscribe, readSaved, readOnServer) as ModelId | null;
  const model = saved && models.includes(saved) ? saved : defaultModel;

  const setModel = useCallback((next: ModelId) => {
    window.localStorage.setItem(STORAGE_KEY, next);
    listeners.forEach((listener) => listener());
  }, []);

  return <ModelContext.Provider value={{ model, models, setModel }}>{children}</ModelContext.Provider>;
}

export function useModel(): ModelState {
  const state = useContext(ModelContext);
  if (!state) throw new Error("useModel must be used inside <ModelProvider>");
  return state;
}
