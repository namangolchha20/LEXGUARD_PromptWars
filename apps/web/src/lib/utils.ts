import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(score: number): string {
  if (score >= 80) return "text-risk-critical";
  if (score >= 60) return "text-risk-high";
  if (score >= 35) return "text-risk-medium";
  return "text-risk-low";
}

export function severityBg(score: number): string {
  if (score >= 80) return "bg-risk-critical/20 border-risk-critical/40";
  if (score >= 60) return "bg-risk-high/20 border-risk-high/40";
  if (score >= 35) return "bg-risk-medium/20 border-risk-medium/40";
  return "bg-risk-low/20 border-risk-low/40";
}

export function priorityColor(priority: string): string {
  switch (priority) {
    case "critical":
      return "bg-risk-critical/15 text-risk-critical border-risk-critical/30";
    case "high":
      return "bg-risk-high/15 text-risk-high border-risk-high/30";
    case "medium":
      return "bg-risk-medium/15 text-risk-medium border-risk-medium/30";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}
