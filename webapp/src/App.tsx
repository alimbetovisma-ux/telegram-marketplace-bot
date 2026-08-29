import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AppProvider, useApp } from "./store";
import { initTelegram, haptic } from "./lib/telegram";
import { BottomNav, type RootTab } from "./components/BottomNav";
import { ToastHost } from "./components/ToastHost";
import { MarketPage } from "./pages/MarketPage";
import { RentPage } from "./pages/RentPage";
import { WalletPage, type WalletTab } from "./pages/WalletPage";
import { ProfilePage } from "./pages/ProfilePage";
import { CategoryListPage } from "./pages/CategoryListPage";
import { ItemDetailPage } from "./pages/ItemDetailPage";
import type { CatalogItem, Category } from "./types";

type SubScreen = { kind: "category"; category: Category } | { kind: "item"; item: CatalogItem };

function Shell() {
  const { loading } = useApp();
  const [activeTab, setActiveTab] = useState<RootTab>("market");
  const [walletTab, setWalletTab] = useState<WalletTab>("topup");
  const [subScreen, setSubScreen] = useState<SubScreen | null>(null);

  useEffect(() => {
    initTelegram();
  }, []);

  const changeTab = (tab: RootTab) => {
    haptic("light");
    setActiveTab(tab);
    setSubScreen(null);
  };

  const goToOrders = () => {
    setActiveTab("wallet");
    setWalletTab("mine");
    setSubScreen(null);
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  let content: ReactNode;
  let key: string;

  if (subScreen?.kind === "item") {
    key = `item-${subScreen.item.id}`;
    content = (
      <ItemDetailPage
        item={subScreen.item}
        onBack={() => setSubScreen({ kind: "category", category: subScreen.item.category })}
        onBought={goToOrders}
        onNeedTopup={() => {
          setActiveTab("wallet");
          setWalletTab("topup");
          setSubScreen(null);
        }}
      />
    );
  } else if (subScreen?.kind === "category") {
    key = `category-${subScreen.category}`;
    content = (
      <CategoryListPage
        category={subScreen.category}
        onBack={() => setSubScreen(null)}
        onOpenItem={(item) => setSubScreen({ kind: "item", item })}
      />
    );
  } else if (activeTab === "market") {
    key = "market";
    content = <MarketPage onSelectCategory={(category) => setSubScreen({ kind: "category", category })} />;
  } else if (activeTab === "rent") {
    key = "rent";
    content = <RentPage onSelectCategory={(category) => setSubScreen({ kind: "category", category })} />;
  } else if (activeTab === "wallet") {
    key = "wallet";
    content = <WalletPage tab={walletTab} onTabChange={setWalletTab} />;
  } else {
    key = "profile";
    content = <ProfilePage onOpenOrders={goToOrders} />;
  }

  return (
    <div className="min-h-screen text-text">
      <ToastHost />
      <AnimatePresence mode="wait">
        <motion.div
          key={key}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -8 }}
          transition={{ duration: 0.18, ease: "easeOut" }}
          className="pb-24"
        >
          {content}
        </motion.div>
      </AnimatePresence>
      <BottomNav active={activeTab} onChange={changeTab} />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
