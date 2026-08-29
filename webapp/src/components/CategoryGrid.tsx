import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import type { Category } from "../types";

const META: Record<Category, { emoji: string; gradient: string; labelKey: string }> = {
  premium: { emoji: "💎", gradient: "linear-gradient(135deg,#4d9eff,#2f6fe0)", labelKey: "cat_premium" },
  stars: { emoji: "⭐️", gradient: "linear-gradient(135deg,#ffd24d,#ff9f4d)", labelKey: "cat_stars" },
  gift_new: { emoji: "🎁", gradient: "linear-gradient(135deg,#ff6fa8,#ff4d7a)", labelKey: "cat_gift_new" },
  gift_old: { emoji: "🏺", gradient: "linear-gradient(135deg,#c084fc,#7c5cff)", labelKey: "cat_gift_old" },
  rent_number: { emoji: "📱", gradient: "linear-gradient(135deg,#3ddc84,#22b563)", labelKey: "cat_rent_number" },
  rent_username: { emoji: "🔗", gradient: "linear-gradient(135deg,#4dd0e1,#3d9be0)", labelKey: "cat_rent_username" },
  rent_nft: { emoji: "🖼", gradient: "linear-gradient(135deg,#7c5cff,#4d9eff)", labelKey: "cat_rent_nft" },
};

export function CategoryGrid({ categories, onSelect }: { categories: Category[]; onSelect: (c: Category) => void }) {
  const { lang } = useApp();

  return (
    <div className="grid grid-cols-2 gap-3 px-4">
      {categories.map((cat, i) => {
        const meta = META[cat];
        return (
          <motion.button
            key={cat}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.04, ease: "easeOut" }}
            whileHover={{ y: -3 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onSelect(cat)}
            className="flex flex-col items-start gap-3 rounded-xl2 border border-border bg-surface p-4 text-left shadow-card"
          >
            <div
              className="flex h-11 w-11 items-center justify-center rounded-2xl text-xl"
              style={{ background: meta.gradient }}
            >
              {meta.emoji}
            </div>
            <span className="text-sm font-semibold leading-tight text-text">{t(lang, meta.labelKey)}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
