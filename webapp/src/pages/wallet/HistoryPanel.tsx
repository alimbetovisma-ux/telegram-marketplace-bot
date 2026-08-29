import { useEffect, useState } from "react";
import { useApp } from "../../store";
import { t } from "../../i18n";
import { api } from "../../lib/api";
import { fmtDate, fmtMoney } from "../../lib/format";
import { ListSkeleton } from "../../components/Skeleton";
import { IconCard, IconStar, IconBag, IconKey, IconGiftBox, IconSettings, IconUndo } from "../../components/icons";
import type { Transaction } from "../../types";
import type { ComponentType } from "react";

const ICON: Record<string, ComponentType<{ className?: string }>> = {
  topup_card: IconCard,
  topup_stars: IconStar,
  purchase: IconBag,
  rent: IconKey,
  referral_bonus: IconGiftBox,
  admin_adjust: IconSettings,
  refund: IconUndo,
};

export function HistoryPanel() {
  const { lang } = useApp();
  const [txs, setTxs] = useState<Transaction[] | null>(null);

  useEffect(() => {
    api.get<Transaction[]>("/api/wallet/history").then(setTxs);
  }, []);

  if (txs === null) return <ListSkeleton count={4} />;
  if (txs.length === 0) return <div className="px-4 py-10 text-center text-sm text-textdim">{t(lang, "history_empty")}</div>;

  return (
    <div className="space-y-2 px-4 pt-2">
      {txs.map((tx) => {
        const positive = Number(tx.amount_uzs) >= 0;
        const Icon = ICON[tx.type];
        return (
          <div key={tx.id} className="flex items-center gap-3 rounded-xl2 border border-border bg-surface p-3 transition-colors hover:bg-surface2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface2 text-textdim">
              {Icon ? <Icon className="h-4 w-4" /> : <span className="h-1.5 w-1.5 rounded-full bg-textdim" />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-text">{tx.type}</div>
              <div className="text-xs text-textdim">{fmtDate(tx.created_at)}</div>
            </div>
            <div className={`shrink-0 text-sm font-bold ${positive ? "text-success" : "text-danger"}`}>
              {positive ? "+" : ""}
              {fmtMoney(tx.amount_uzs)} {t(lang, "som")}
            </div>
          </div>
        );
      })}
    </div>
  );
}
