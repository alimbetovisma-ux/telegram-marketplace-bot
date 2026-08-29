import { useState } from "react";
import { motion } from "framer-motion";
import { useApp } from "../../store";
import { t } from "../../i18n";
import { api } from "../../lib/api";
import { fmtMoney } from "../../lib/format";
import { getTelegram, hapticSuccess, openInvoice } from "../../lib/telegram";
import { IconCard, IconStar } from "../../components/icons";
import type { CardTopupResult, StarsTopupResult } from "../../types";

const QUICK_AMOUNTS = [20000, 50000, 100000, 250000, 500000];

export function TopupPanel() {
  const { lang, refreshMe, showToast } = useApp();
  const [method, setMethod] = useState<"card" | "stars">("card");
  const [amount, setAmount] = useState("50000");
  const [busy, setBusy] = useState(false);
  const [cardResult, setCardResult] = useState<CardTopupResult | null>(null);

  const numericAmount = Number(amount.replace(/\s/g, ""));
  const valid = Number.isFinite(numericAmount) && numericAmount > 0;

  const handleCard = async () => {
    if (!valid || busy) return;
    setBusy(true);
    try {
      const res = await api.post<CardTopupResult>("/api/wallet/topup/card", { amount_uzs: numericAmount });
      setCardResult(res);
    } catch (e) {
      showToast(String(e), "error");
    } finally {
      setBusy(false);
    }
  };

  const handleStars = async () => {
    if (!valid || busy) return;
    setBusy(true);
    try {
      const res = await api.post<StarsTopupResult>("/api/wallet/topup/stars", { amount_uzs: numericAmount });
      const status = await openInvoice(res.invoice_link);
      if (status === "paid") {
        hapticSuccess();
        showToast(t(lang, "topup_stars_success"), "success");
        setTimeout(() => refreshMe(), 1500);
      }
    } catch (e) {
      showToast(String(e), "error");
    } finally {
      setBusy(false);
    }
  };

  const openBotChat = () => {
    const tg = getTelegram();
    if (tg && cardResult) tg.openTelegramLink(cardResult.bot_deeplink);
  };

  if (cardResult) {
    return (
      <div className="space-y-4 px-4 pt-2">
        <div className="rounded-xl2 border border-border bg-surface p-4">
          <div className="text-sm text-textdim">{t(lang, "topup_card_result_title")}</div>
          <div className="mt-2 rounded-xl bg-surface2 px-4 py-3 text-center font-mono text-lg tracking-widest text-text">
            {cardResult.card_number}
          </div>
          <div className="mt-2 text-center text-sm text-textdim">
            {t(lang, "topup_card_holder")}: {cardResult.card_holder}
          </div>
          <div className="mt-3 text-center text-sm font-semibold text-text">
            {fmtMoney(cardResult.amount_uzs)} {t(lang, "som")}
          </div>
        </div>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={openBotChat}
          className="w-full rounded-2xl py-3.5 text-base font-semibold text-white shadow-glow"
          style={{ background: "linear-gradient(135deg,#4d9eff,#7c5cff)" }}
        >
          {t(lang, "topup_go_to_bot")}
        </motion.button>
        <button onClick={() => setCardResult(null)} className="w-full py-2 text-sm text-textdim">
          {t(lang, "back")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4 px-4 pt-2">
      <div className="flex gap-2 rounded-2xl bg-surface p-1.5">
        {(["card", "stars"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMethod(m)}
            className={`relative flex flex-1 items-center justify-center gap-1.5 rounded-xl py-2.5 text-sm font-semibold transition-colors ${
              method === m ? "bg-accent text-white" : "text-textdim"
            }`}
          >
            {m === "card" ? <IconCard className="h-4 w-4" /> : <IconStar className="h-4 w-4" />}
            {t(lang, m === "card" ? "topup_method_card" : "topup_method_stars")}
          </button>
        ))}
      </div>

      <div>
        <div className="mb-1.5 text-xs font-medium text-textdim">{t(lang, "topup_amount_label")}</div>
        <input
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ""))}
          inputMode="numeric"
          className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-lg font-semibold text-text outline-none focus:border-accent"
          placeholder="50000"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {QUICK_AMOUNTS.map((v) => (
          <button
            key={v}
            onClick={() => setAmount(String(v))}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
              numericAmount === v ? "border-accent bg-accent/15 text-accent" : "border-border text-textdim"
            }`}
          >
            {fmtMoney(v)}
          </button>
        ))}
      </div>

      {!valid && amount.length > 0 && <div className="text-xs text-danger">{t(lang, "topup_invalid_amount")}</div>}

      <motion.button
        whileTap={{ scale: 0.97 }}
        disabled={!valid || busy}
        onClick={method === "card" ? handleCard : handleStars}
        className="w-full rounded-2xl py-3.5 text-base font-semibold text-white shadow-glow disabled:opacity-50"
        style={{ background: "linear-gradient(135deg,#4d9eff,#7c5cff)" }}
      >
        {t(lang, method === "card" ? "topup_get_card" : "topup_pay_stars")}
      </motion.button>
    </div>
  );
}
