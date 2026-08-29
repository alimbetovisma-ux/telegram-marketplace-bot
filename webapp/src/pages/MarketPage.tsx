import { useApp } from "../store";
import { t } from "../i18n";
import { CategoryGrid } from "../components/CategoryGrid";
import type { Category } from "../types";

const CATEGORIES: Category[] = ["premium", "stars", "gift_new", "gift_old"];

export function MarketPage({ onSelectCategory }: { onSelectCategory: (c: Category) => void }) {
  const { lang } = useApp();

  return (
    <div className="pb-4 pt-[max(14px,env(safe-area-inset-top))]">
      <div className="px-4 pb-4">
        <h1 className="text-2xl font-bold text-text">{t(lang, "market_title")}</h1>
        <p className="mt-0.5 text-sm text-textdim">{t(lang, "market_sub")}</p>
      </div>
      <CategoryGrid categories={CATEGORIES} onSelect={onSelectCategory} />
    </div>
  );
}
