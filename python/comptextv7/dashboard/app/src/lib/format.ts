export const number = new Intl.NumberFormat('en-US');
export const compactNumber = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
export const percent = (value: number, fractionDigits = 1) => `${value.toFixed(fractionDigits)}%`;
export const ratio = (value: number) => `${value.toFixed(value > 100 ? 0 : 1)}×`;
export const ms = (value: number) => `${number.format(Math.round(value))} ms`;

export function relativeTime(iso: string): string {
  const delta = Date.now() - new Date(iso).getTime();
  const minutes = Math.max(0, Math.round(delta / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
