import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { fmtMoney } from "../lib/format";

export function BalanceCard({ onTopup }: { onTopup?: () => void }) {
  const { me, lang } = useApp();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="relative overflow-hidden rounded-xl2 p-5 shadow-glow"
      style={{ background: "linear-gradient(135deg, #4d9eff 0%, #7c5cff 100%)" }}
    >
      <div className="pointer-events-none absolute -right-8 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-12 -left-6 h-32 w-32 rounded-full bg-black/10 blur-2xl" />

      <div className="relative z-10 text-xs font-semibold tracking-wider text-white/75">{t(lang, "balance_label")}</div>
      <div className="tabular-nums relative z-10 mt-1 font-mono text-3xl font-medium text-white">
        {fmtMoney(me?.balance ?? 0)} <span className="font-sans text-lg font-semibold text-white/80">{t(lang, "som")}</span>
      </div>

      {onTopup && (
        <button
          onClick={onTopup}
          className="relative z-10 mt-4 rounded-full bg-white/15 px-4 py-2 text-sm font-semibold text-white backdrop-blur-md transition-transform active:scale-95"
        >
          + {t(lang, "wallet_topup")}
        </button>
      )}
    </motion.div>
  );
}
