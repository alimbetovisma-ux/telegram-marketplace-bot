import { motion } from "framer-motion";
import { useApp } from "../store";
import { t } from "../i18n";
import { IconMarket, IconProfile, IconRent, IconWallet } from "./icons";

export type RootTab = "market" | "rent" | "wallet" | "profile";

const TABS: { key: RootTab; icon: (p: { className?: string }) => JSX.Element; labelKey: string }[] = [
  { key: "market", icon: IconMarket, labelKey: "nav_market" },
  { key: "rent", icon: IconRent, labelKey: "nav_rent" },
  { key: "wallet", icon: IconWallet, labelKey: "nav_wallet" },
  { key: "profile", icon: IconProfile, labelKey: "nav_profile" },
];

export function BottomNav({ active, onChange }: { active: RootTab; onChange: (tab: RootTab) => void }) {
  const { lang } = useApp();

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 px-3 pb-[max(10px,env(safe-area-inset-bottom))] pt-2">
      <div className="glass mx-auto flex max-w-md items-stretch justify-between rounded-2xl px-1.5 py-1.5 shadow-card">
        {TABS.map(({ key, icon: Icon, labelKey }) => {
          const isActive = active === key;
          return (
            <button
              key={key}
              onClick={() => onChange(key)}
              className="relative flex flex-1 flex-col items-center gap-0.5 rounded-xl py-2 text-[11px] font-medium transition-colors"
            >
              {isActive && (
                <motion.div
                  layoutId="nav-pill"
                  className="absolute inset-0 rounded-xl bg-white/[0.07]"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
              <Icon className={`relative z-10 h-5 w-5 ${isActive ? "text-accent" : "text-textdim"}`} />
              <span className={`relative z-10 ${isActive ? "text-text" : "text-textdim"}`}>{t(lang, labelKey)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
