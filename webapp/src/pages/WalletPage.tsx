import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { BalanceCard } from "../components/BalanceCard";
import { TopupPanel } from "./wallet/TopupPanel";
import { OrdersPanel } from "./wallet/OrdersPanel";
import { HistoryPanel } from "./wallet/HistoryPanel";

export type WalletTab = "topup" | "withdraw" | "mine" | "history";
const TABS: WalletTab[] = ["topup", "withdraw", "mine", "history"];
const TAB_LABEL: Record<WalletTab, string> = {
  topup: "wallet_topup",
  withdraw: "wallet_withdraw",
  mine: "wallet_mine",
  history: "wallet_history",
};

export function WalletPage({ tab, onTabChange }: { tab: WalletTab; onTabChange: (tab: WalletTab) => void }) {
  const { lang } = useApp();

  return (
    <div className="pb-4 pt-[max(14px,env(safe-area-inset-top))]">
      <div className="px-4">
        <BalanceCard />
      </div>

      <div className="no-scrollbar mt-4 flex gap-1.5 overflow-x-auto px-4">
        {TABS.map((tb) => {
          const active = tab === tb;
          return (
            <button
              key={tb}
              onClick={() => onTabChange(tb)}
              className={`relative shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                active ? "text-white" : "text-textdim"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="wallet-tab-pill"
                  className="absolute inset-0 rounded-full bg-accent"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
              <span className="relative z-10">{t(lang, TAB_LABEL[tb])}</span>
            </button>
          );
        })}
      </div>

      <div className="mt-4">
        {tab === "topup" && <TopupPanel />}
        {tab === "withdraw" && (
          <div className="px-4 py-10 text-center text-sm text-textdim">{t(lang, "withdraw_soon")}</div>
        )}
        {tab === "mine" && <OrdersPanel />}
        {tab === "history" && <HistoryPanel />}
      </div>
    </div>
  );
}
