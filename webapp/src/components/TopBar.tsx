import { IconBack } from "./icons";

export function TopBar({ title, onBack }: { title: string; onBack?: () => void }) {
  return (
    <div className="sticky top-0 z-30 flex items-center gap-2 bg-bg/80 px-4 pb-3 pt-[max(14px,env(safe-area-inset-top))] backdrop-blur-xl">
      {onBack && (
        <button
          onClick={onBack}
          className="-ml-1 flex h-9 w-9 items-center justify-center rounded-full text-text active:scale-90 transition-transform"
        >
          <IconBack className="h-5 w-5" />
        </button>
      )}
      <h1 className="font-display text-lg font-semibold text-text">{title}</h1>
    </div>
  );
}
