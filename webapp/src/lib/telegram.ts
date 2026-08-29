interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      username?: string;
      first_name?: string;
      photo_url?: string;
      language_code?: string;
    };
  };
  themeParams: Record<string, string>;
  colorScheme: "light" | "dark";
  ready: () => void;
  expand: () => void;
  close: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  openTelegramLink: (url: string) => void;
  openInvoice: (url: string, callback?: (status: string) => void) => void;
  openLink: (url: string) => void;
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
  };
  MainButton: {
    show: () => void;
    hide: () => void;
    setText: (text: string) => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;

export function getTelegram(): TelegramWebApp | undefined {
  return tg;
}

export function initTelegram(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  try {
    tg.setBackgroundColor("#0b0e14");
    tg.setHeaderColor("#0b0e14");
  } catch {
    /* older client, ignore */
  }
}

export function haptic(style: "light" | "medium" | "heavy" = "light"): void {
  tg?.HapticFeedback?.impactOccurred(style);
}

export function hapticSuccess(): void {
  tg?.HapticFeedback?.notificationOccurred("success");
}

export function hapticError(): void {
  tg?.HapticFeedback?.notificationOccurred("error");
}

export function getInitData(): string {
  return tg?.initData ?? "";
}

export function getTelegramUser() {
  return tg?.initDataUnsafe?.user;
}

export function openInvoice(url: string): Promise<string> {
  return new Promise((resolve) => {
    if (!tg) {
      resolve("cancelled");
      return;
    }
    tg.openInvoice(url, (status) => resolve(status));
  });
}
