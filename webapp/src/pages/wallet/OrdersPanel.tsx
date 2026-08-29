import { useEffect, useState } from "react";
import { useApp } from "../../store";
import { t } from "../../i18n";
import { api } from "../../lib/api";
import { fmtDate, fmtMoney } from "../../lib/format";
import { ListSkeleton } from "../../components/Skeleton";
import type { Order } from "../../types";

const STATUS_COLOR: Record<string, string> = {
  paid_awaiting_fulfillment: "text-accent",
  fulfilled: "text-success",
  cancelled: "text-danger",
};

export function OrdersPanel() {
  const { lang } = useApp();
  const [orders, setOrders] = useState<Order[] | null>(null);

  useEffect(() => {
    api.get<Order[]>("/api/orders").then(setOrders);
  }, []);

  if (orders === null) return <ListSkeleton count={3} />;
  if (orders.length === 0) return <div className="px-4 py-10 text-center text-sm text-textdim">{t(lang, "orders_empty")}</div>;

  return (
    <div className="space-y-2.5 px-4 pt-2">
      {orders.map((o) => (
        <div key={o.id} className="rounded-xl2 border border-border bg-surface p-3.5">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-text">
                #{o.id} {o.item_title}
              </div>
              <div className="mt-0.5 text-xs text-textdim">{fmtDate(o.created_at)}</div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-sm font-bold text-text">
                {fmtMoney(o.total_uzs)} {t(lang, "som")}
              </div>
              <div className={`mt-0.5 text-xs font-medium ${STATUS_COLOR[o.status] ?? "text-textdim"}`}>
                {t(lang, `status_${o.status}`)}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
