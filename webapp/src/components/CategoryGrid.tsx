import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { IconGem, IconStar, IconGiftBox, IconRelic, IconPhone, IconLink, IconFrame } from "./icons";
import type { Category } from "../types";
import type { ComponentType, CSSProperties } from "react";

const META: Record<Category, { Icon: ComponentType<{ className?: string }>; glow: string; gradient: string; labelKey: string }> = {
  premium: { Icon: IconGem, glow: "#6c8bff", gradient: "linear-gradient(135deg,#6c8bff,#3f66d6)", labelKey: "cat_premium" },
  stars: { Icon: IconStar, glow: "#ffb84d", gradient: "linear-gradient(135deg,#ffd24d,#ff9f4d)", labelKey: "cat_stars" },
  gift_new: { Icon: IconGiftBox, glow: "#ff6fa8", gradient: "linear-gradient(135deg,#ff6fa8,#ff4d7a)", labelKey: "cat_gift_new" },
  gift_old: { Icon: IconRelic, glow: "#c084fc", gradient: "linear-gradient(135deg,#c084fc,#7c5cff)", labelKey: "cat_gift_old" },
  rent_number: { Icon: IconPhone, glow: "#33d6ac", gradient: "linear-gradient(135deg,#3ddc84,#22b563)", labelKey: "cat_rent_number" },
  rent_username: { Icon: IconLink, glow: "#4dd0e1", gradient: "linear-gradient(135deg,#4dd0e1,#3d9be0)", labelKey: "cat_rent_username" },
  rent_nft: { Icon: IconFrame, glow: "#7c5cff", gradient: "linear-gradient(135deg,#7c5cff,#4d9eff)", labelKey: "cat_rent_nft" },
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
            whileHover={{ y: -3, boxShadow: "0 10px 26px -8px rgba(0,0,0,0.4)" }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onSelect(cat)}
            style={{ "--glow": meta.glow } as CSSProperties}
            className="glass glow-tile flex flex-col items-start gap-3 rounded-xl2 p-4 text-left shadow-tile transition-colors"
          >
            <motion.div
              whileHover={{ scale: 1.08, rotate: 3 }}
              className="flex h-11 w-11 items-center justify-center rounded-2xl text-white"
              style={{ background: meta.gradient }}
            >
              <meta.Icon className="h-5 w-5" />
            </motion.div>
            <span className="text-sm font-semibold leading-tight text-text">{t(lang, meta.labelKey)}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
