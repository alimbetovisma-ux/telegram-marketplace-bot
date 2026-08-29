import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { fmtMoney } from "../lib/format";
import type { CatalogItem } from "../types";

const RENT_CATEGORIES = new Set(["rent_number", "rent_username", "rent_nft"]);

export function ItemCard({ item, onOpen, index = 0 }: { item: CatalogItem; onOpen: () => void; index?: number }) {
  const { lang } = useApp();
  const isRent = RENT_CATEGORIES.has(item.category);

  return (
    <motion.button
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.03, 0.3) }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.985 }}
      onClick={onOpen}
      className="flex w-full items-center gap-3 rounded-xl2 border border-border bg-surface p-3 text-left shadow-card"
    >
      <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-surface2 text-2xl">
        {item.image_url ? <img src={item.image_url} alt="" className="h-full w-full object-cover" /> : "🛍"}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold text-text">{item.title}</div>
        <div className="mt-0.5 flex items-center gap-1.5">
          <span className="text-sm font-bold text-accent">{fmtMoney(item.price_uzs)}</span>
          <span className="text-xs text-textdim">{t(lang, "som")}</span>
          {isRent && <span className="text-xs text-textdim">{t(lang, "per_day")}</span>}
          {item.discount_percent > 0 && (
            <span className="rounded-md bg-danger/15 px-1.5 py-0.5 text-[10px] font-bold text-danger">
              -{item.discount_percent}%
            </span>
          )}
        </div>
      </div>
      <span className="shrink-0 rounded-full bg-accent/15 px-3 py-1.5 text-xs font-semibold text-accent">
        {t(lang, isRent ? "btn_rent" : "btn_buy")}
      </span>
    </motion.button>
  );
}
