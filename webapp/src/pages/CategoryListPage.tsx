import { useEffect, useState } from "react";
import { useApp } from "../store";
import { t } from "../i18n";
import { api } from "../lib/api";
import { TopBar } from "../components/TopBar";
import { ItemCard } from "../components/ItemCard";
import { ListSkeleton } from "../components/Skeleton";
import type { CatalogItem, Category } from "../types";

export function CategoryListPage({
  category,
  onBack,
  onOpenItem,
}: {
  category: Category;
  onBack: () => void;
  onOpenItem: (item: CatalogItem) => void;
}) {
  const { lang } = useApp();
  const [items, setItems] = useState<CatalogItem[] | null>(null);

  useEffect(() => {
    setItems(null);
    api.get<CatalogItem[]>(`/api/catalog?category=${category}`).then(setItems);
  }, [category]);

  return (
    <div className="pb-4">
      <TopBar title={t(lang, `cat_${category}`)} onBack={onBack} />
      {items === null ? (
        <ListSkeleton />
      ) : items.length === 0 ? (
        <div className="px-4 py-16 text-center text-sm text-textdim">{t(lang, "empty_category")}</div>
      ) : (
        <div className="space-y-2.5 px-4">
          {items.map((item, i) => (
            <ItemCard key={item.id} item={item} index={i} onOpen={() => onOpenItem(item)} />
          ))}
        </div>
      )}
    </div>
  );
}
