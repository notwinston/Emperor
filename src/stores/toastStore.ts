import { create } from "zustand";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

let toastId = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = `toast-${++toastId}`;
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    };

    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));

    // Auto-remove after duration (unless duration is 0)
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, newToast.duration);
    }

    return id;
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  clearToasts: () => set({ toasts: [] }),
}));

// Convenience functions
export const toast = {
  success: (title: string, message?: string) =>
    useToastStore.getState().addToast({ type: "success", title, message }),

  error: (title: string, message?: string) =>
    useToastStore.getState().addToast({ type: "error", title, message }),

  warning: (title: string, message?: string) =>
    useToastStore.getState().addToast({ type: "warning", title, message }),

  info: (title: string, message?: string) =>
    useToastStore.getState().addToast({ type: "info", title, message }),

  custom: (toast: Omit<Toast, "id">) =>
    useToastStore.getState().addToast(toast),
};
