import { AnimatePresence, motion } from "framer-motion";
import { useApp } from "../store";

export function ToastHost() {
  const { toasts } = useApp();

  return (
    <div className="pointer-events-none fixed left-0 right-0 top-[max(10px,env(safe-area-inset-top))] z-[60] flex flex-col items-center gap-2 px-4">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: -16, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className={`glass max-w-sm rounded-xl px-4 py-2.5 text-sm font-medium shadow-card ${
              toast.variant === "error" ? "text-danger" : "text-success"
            }`}
          >
            {toast.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
