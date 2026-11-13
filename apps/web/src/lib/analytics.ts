import type { Dashboard, Filters } from "../types.ts";

export const EMPTY_FILTERS: Filters = {
  start_date: "",
  end_date: "",
  category: "",
  channel: "",
  device: "",
};
export const number = (value: number) =>
  new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);
export const percent = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
export const duration = (seconds: number) =>
  `${Math.floor(Math.round(seconds) / 60)}m ${String(Math.round(seconds) % 60).padStart(2, "0")}s`;
export function dateLabel(value: string, year = false) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    ...(year ? { year: "numeric" } : {}),
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}
export function apiUrl(path: string, filters: Filters): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters))
    if (value) query.set(key, value);
  return query.size ? `${path}?${query.toString()}` : path;
}
export function validateDates(filters: Filters) {
  return filters.start_date &&
    filters.end_date &&
    filters.start_date > filters.end_date
    ? "The start date must be on or before the end date."
    : "";
}

/** The repository omits dates with no matching sessions. Preserve calendar spacing. */
export function completeDailySeries(
  rows: Dashboard["daily"],
  startDate: string,
  endDate: string,
): Dashboard["daily"] {
  const start = Date.parse(`${startDate}T00:00:00Z`);
  const end = Date.parse(`${endDate}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start)
    return [];
  const byDate = new Map(rows.map((row) => [row.date, row]));
  const result: Dashboard["daily"] = [];
  for (let timestamp = start; timestamp <= end; timestamp += 86_400_000) {
    const date = new Date(timestamp).toISOString().slice(0, 10);
    result.push(byDate.get(date) ?? { date, sessions: 0, subscriptions: 0 });
  }
  return result;
}
