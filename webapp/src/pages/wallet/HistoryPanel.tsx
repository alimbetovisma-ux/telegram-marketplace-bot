import { useEffect, useState } from "react";
import { useApp } from "../../store";
import { t } from "../../i18n";
import { api } from "../../lib/api";
import { fmtDate, fmtMoney } from "../../lib/format";
import { ListSkeleton } from "../../components/Skeleton";
import type { Transaction } from "../../types";

const ICON: Record<string, string> = {
  topup_card: "💳",
  topup_stars: "⭐️",
  purchase: "🛒",
  rent: "🔑",
  referral_bonus: "🎁",
  admin_adjust: "⚙️",
  refund: "↩️",
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
        return (
          <div key={tx.id} className="flex items-center gap-3 rounded-xl2 border border-border bg-surface p-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface2 text-base">
              {ICON[tx.type] ?? "•"}
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
