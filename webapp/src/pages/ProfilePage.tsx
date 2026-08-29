import { useState } from "react";
import { motion } from "framer-motion";
import { useApp } from "../store";
import { t, type Lang } from "../i18n";
import { getTelegramUser, haptic } from "../lib/telegram";
import { fmtMoney } from "../lib/format";
import { IconCopy } from "../components/icons";

const LANGUAGES: { code: Lang; label: string }[] = [
  { code: "uz", label: "🇺🇿 O'zbek" },
  { code: "ru", label: "🇷🇺 Русский" },
  { code: "en", label: "🇬🇧 English" },
];

export function ProfilePage({ onOpenOrders }: { onOpenOrders: () => void }) {
  const { me, lang, setLanguage } = useApp();
  const [copied, setCopied] = useState(false);
  const tgUser = getTelegramUser();

  const handleCopy = async () => {
    if (!me) return;
    try {
      await navigator.clipboard.writeText(me.referral_link);
      haptic("medium");
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="space-y-4 px-4 pb-4 pt-[max(14px,env(safe-area-inset-top))]">
      <div className="flex items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-accent to-accent2 text-xl font-bold text-white">
          {tgUser?.photo_url ? (
            <img src={tgUser.photo_url} alt="" className="h-full w-full object-cover" />
          ) : (
            (me?.first_name ?? "?").slice(0, 1).toUpperCase()
          )}
        </div>
        <div className="min-w-0">
          <div className="truncate text-lg font-bold text-text">{me?.first_name}</div>
          <div className="truncate text-sm text-textdim">{me?.username ? `@${me.username}` : `ID ${me?.tg_id}`}</div>
        </div>
      </div>

      <div className="rounded-xl2 border border-border bg-surface p-4">
        <div className="text-xs font-medium text-textdim">{t(lang, "balance_label")}</div>
        <div className="mt-1 text-2xl font-bold text-text">
          {fmtMoney(me?.balance ?? 0)} <span className="text-base font-semibold text-textdim">{t(lang, "som")}</span>
        </div>
      </div>

      <button
        onClick={onOpenOrders}
        className="w-full rounded-xl2 border border-border bg-surface p-4 text-left text-sm font-semibold text-text"
      >
        {t(lang, "profile_my_orders")}
      </button>

      <div className="rounded-xl2 border border-border bg-surface p-4">
        <div className="mb-2.5 text-sm font-semibold text-text">{t(lang, "profile_language")}</div>
        <div className="flex gap-2">
          {LANGUAGES.map(({ code, label }) => {
            const active = lang === code;
            return (
              <motion.button
                key={code}
                whileTap={{ scale: 0.95 }}
                onClick={() => setLanguage(code)}
                className={`flex-1 rounded-xl border py-2 text-xs font-semibold transition-colors ${
                  active ? "border-accent bg-accent/15 text-accent" : "border-border text-textdim"
                }`}
              >
                {label}
              </motion.button>
            );
          })}
        </div>
      </div>

      <div className="rounded-xl2 p-4 shadow-glow" style={{ background: "linear-gradient(135deg,#7c5cff,#4d9eff)" }}>
        <div className="text-sm font-bold text-white">{t(lang, "profile_referral_title")}</div>
        <div className="mt-1 text-xs text-white/80">{t(lang, "profile_referral_desc", { percent: "5" })}</div>
        <button
          onClick={handleCopy}
          className="mt-3 flex w-full items-center justify-between gap-2 rounded-xl bg-white/15 px-3.5 py-2.5 text-left backdrop-blur-md"
        >
          <span className="truncate text-xs font-medium text-white">{me?.referral_link}</span>
          <IconCopy className="h-4 w-4 shrink-0 text-white" />
        </button>
        {copied && <div className="mt-1.5 text-xs font-medium text-white">{t(lang, "profile_copied")}</div>}
      </div>
    </div>
  );
}
