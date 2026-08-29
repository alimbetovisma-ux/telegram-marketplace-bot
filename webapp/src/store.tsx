import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./lib/api";
import type { Lang } from "./i18n";
import type { Me } from "./types";

export interface Toast {
  id: number;
  message: string;
  variant: "success" | "error";
}

interface AppState {
  me: Me | null;
  lang: Lang;
  loading: boolean;
  refreshMe: () => Promise<void>;
  setLanguage: (lang: Lang) => Promise<void>;
  toasts: Toast[];
  showToast: (message: string, variant?: Toast["variant"]) => void;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const refreshMe = async () => {
    const data = await api.get<Me>("/api/me");
    setMe(data);
  };

  useEffect(() => {
    refreshMe().finally(() => setLoading(false));
  }, []);

  const setLanguage = async (lang: Lang) => {
    const data = await api.post<Me>("/api/me/language", { language: lang });
    setMe(data);
  };

  const showToast = (message: string, variant: Toast["variant"] = "success") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => setToasts((prev) => prev.filter((toast) => toast.id !== id)), 3000);
  };

  return (
    <AppContext.Provider value={{ me, lang: me?.language ?? "uz", loading, refreshMe, setLanguage, toasts, showToast }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
