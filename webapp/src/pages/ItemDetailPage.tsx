import { useState } from "react";
import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { api, ApiError } from "../lib/api";
import { fmtMoney } from "../lib/format";
import { TopBar } from "../components/TopBar";
import { hapticError, hapticSuccess } from "../lib/telegram";
import type { CatalogItem, Order } from "../types";

const RENT_CATEGORIES = new Set(["rent_number", "rent_username", "rent_nft"]);

export function ItemDetailPage({
  item,
  onBack,
  onBought,
  onNeedTopup,
}: {
  item: CatalogItem;
  onBack: () => void;
  onBought: () => void;
  onNeedTopup: () => void;
}) {
  const { lang, refreshMe, showToast } = useApp();
  const [busy, setBusy] = useState(false);
  const isRent = RENT_CATEGORIES.has(item.category);

  const handleBuy = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post<Order>("/api/orders", { catalog_item_id: item.id });
      hapticSuccess();
      showToast(t(lang, "buy_success"), "success");
      await refreshMe();
      onBought();
    } catch (e) {
      hapticError();
      if (e instanceof ApiError && e.status === 402) {
        showToast(t(lang, "buy_insufficient"), "error");
        onNeedTopup();
      } else {
        showToast(String(e), "error");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="pb-28">
      <TopBar title="" onBack={onBack} />
      <div className="px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex h-56 w-full items-center justify-center overflow-hidden rounded-xl2 border border-border bg-surface text-6xl"
        >
          {item.image_url ? <img src={item.image_url} alt="" className="h-full w-full object-cover" /> : "🛍"}
        </motion.div>

        <h1 className="mt-4 text-xl font-bold text-text">{item.title}</h1>
        {item.description && <p className="mt-1.5 text-sm leading-relaxed text-textdim">{item.description}</p>}

        <div className="mt-4 flex items-center gap-2">
          <span className="text-2xl font-bold text-accent">{fmtMoney(item.price_uzs)}</span>
          <span className="text-sm text-textdim">
            {t(lang, "som")}
            {isRent ? ` ${t(lang, "per_day")}` : ""}
          </span>
          {item.discount_percent > 0 && (
            <span className="rounded-md bg-danger/15 px-2 py-0.5 text-xs font-bold text-danger">
              -{item.discount_percent}%
            </span>
          )}
        </div>
      </div>

      <div className="fixed bottom-[calc(72px+env(safe-area-inset-bottom))] left-0 right-0 px-4">
        <motion.button
          whileTap={{ scale: 0.97 }}
          disabled={busy}
          onClick={handleBuy}
          className="w-full rounded-2xl py-3.5 text-base font-semibold text-white shadow-glow disabled:opacity-60"
          style={{ background: "linear-gradient(135deg,#4d9eff,#7c5cff)" }}
        >
          {t(lang, isRent ? "btn_rent" : "btn_buy")} — {fmtMoney(item.price_uzs)} {t(lang, "som")}
        </motion.button>
      </div>
    </div>
  );
}
