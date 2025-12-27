import { motion, AnimatePresence } from "framer-motion";
import { useToastStore, Toast as ToastType, ToastType as ToastVariant } from "@/stores/toastStore";
import { cn } from "@/lib/utils";

const icons: Record<ToastVariant, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

const styles: Record<ToastVariant, string> = {
  success: "border-green-500/50 bg-green-500/10",
  error: "border-red-500/50 bg-red-500/10",
  warning: "border-amber-500/50 bg-amber-500/10",
  info: "border-blue-500/50 bg-blue-500/10",
};

const iconStyles: Record<ToastVariant, string> = {
  success: "bg-green-500 text-white",
  error: "bg-red-500 text-white",
  warning: "bg-amber-500 text-black",
  info: "bg-blue-500 text-white",
};

function ToastItem({ toast }: { toast: ToastType }) {
  const { removeToast } = useToastStore();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.9 }}
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border backdrop-blur-sm",
        "shadow-lg shadow-black/20 max-w-sm w-full",
        styles[toast.type]
      )}
    >
      <div
        className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0",
          iconStyles[toast.type]
        )}
      >
        {icons[toast.type]}
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-foreground">{toast.title}</p>
        {toast.message && (
          <p className="text-sm text-muted-foreground mt-0.5">{toast.message}</p>
        )}
        {toast.action && (
          <button
            onClick={() => {
              toast.action?.onClick();
              removeToast(toast.id);
            }}
            className="text-sm text-amber-500 hover:text-amber-400 mt-2 font-medium"
          >
            {toast.action.label}
          </button>
        )}
      </div>

      <button
        onClick={() => removeToast(toast.id)}
        className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </motion.div>
  );
}

export function ToastContainer() {
  const { toasts } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
}
