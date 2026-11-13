import test from "node:test";
import assert from "node:assert/strict";
import {
  apiUrl,
  completeDailySeries,
  EMPTY_FILTERS,
  validateDates,
  duration,
  percent,
} from "./analytics.ts";

test("query parameters preserve names safely and omit unset filters", () => {
  const result = apiUrl("/api/v1/dashboard", {
    ...EMPTY_FILTERS,
    category: "Markets & Economy",
  });
  assert.equal(
    new URL(result, "https://presslens.example").searchParams.get("category"),
    "Markets & Economy",
  );
  assert.equal(apiUrl("/api/v1/dashboard", EMPTY_FILTERS), "/api/v1/dashboard");
});
test("date ranges reject reversed bounds while allowing a single day", () => {
  assert.ok(
    validateDates({
      ...EMPTY_FILTERS,
      start_date: "2026-09-02",
      end_date: "2026-09-01",
    }),
  );
  assert.equal(
    validateDates({
      ...EMPTY_FILTERS,
      start_date: "2026-09-01",
      end_date: "2026-09-01",
    }),
    "",
  );
});
test("rates and rounded durations display correctly at boundaries", () => {
  assert.equal(percent(0), "0.0%");
  assert.equal(percent(0.025), "2.5%");
  assert.equal(duration(59.7), "1m 00s");
});
test("daily chart retains zero-session dates and inclusive boundaries", () => {
  const rows = [{ date: "2026-09-03", sessions: 9, subscriptions: 1 }];
  assert.deepEqual(completeDailySeries(rows, "2026-09-01", "2026-09-04"), [
    { date: "2026-09-01", sessions: 0, subscriptions: 0 },
    { date: "2026-09-02", sessions: 0, subscriptions: 0 },
    rows[0],
    { date: "2026-09-04", sessions: 0, subscriptions: 0 },
  ]);
});
test("daily chart supports one date and empty data without invalid timestamps", () => {
  assert.deepEqual(completeDailySeries([], "2026-09-01", "2026-09-01"), [
    { date: "2026-09-01", sessions: 0, subscriptions: 0 },
  ]);
  assert.deepEqual(completeDailySeries([], "", ""), []);
  assert.deepEqual(completeDailySeries([], "2026-09-02", "2026-09-01"), []);
});
