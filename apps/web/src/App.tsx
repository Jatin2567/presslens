import { useEffect, useId, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import type { Dashboard, FilterOptions, Filters } from "./types";
import {
  apiUrl,
  completeDailySeries,
  dateLabel,
  duration,
  EMPTY_FILTERS,
  number,
  percent,
  validateDates,
} from "./lib/analytics";

async function readJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok)
    throw new Error(
      `The analytics service returned ${response.status}. Please try again.`,
    );
  return response.json() as Promise<T>;
}

function Icon({
  name,
  size = 18,
}: {
  name: "grid" | "chart" | "file" | "arrow" | "download" | "reset" | "filter";
  size?: number;
}) {
  const shapes: Record<typeof name, ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    chart: (
      <>
        <path d="M4 3v17h17M8 15v-4m5 4V7m5 8V4" />
      </>
    ),
    file: (
      <>
        <path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8m-8 4h6" />
      </>
    ),
    arrow: (
      <>
        <path d="M5 12h14m-6-6 6 6-6 6" />
      </>
    ),
    download: (
      <>
        <path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5" />
      </>
    ),
    reset: (
      <>
        <path d="M4 9a8 8 0 1 1-.2 6M4 3v6h6" />
      </>
    ),
    filter: (
      <>
        <path d="M3 5h18M6 12h12m-9 7h6" />
        <circle cx="8" cy="5" r="2" />
        <circle cx="16" cy="12" r="2" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {shapes[name]}
    </svg>
  );
}

function TrendChart({
  rows: sourceRows,
  startDate,
  endDate,
}: {
  rows: Dashboard["daily"];
  startDate: string;
  endDate: string;
}) {
  const id = useId();
  const [tableOpen, setTableOpen] = useState(false);
  const rows = completeDailySeries(sourceRows, startDate, endDate);
  if (!rows.length)
    return (
      <p className="chart-empty">
        No daily data is available for this date range.
      </p>
    );
  const width = 820,
    height = 250,
    left = 44,
    right = 12,
    top = 18,
    bottom = 36;
  const max = Math.max(...rows.map((row) => row.sessions));
  const ceiling = Math.max(4, Math.ceil(max / 4) * 4);
  const chartWidth = width - left - right,
    chartHeight = height - top - bottom;
  const x = (index: number) =>
    left +
    (rows.length === 1
      ? chartWidth / 2
      : (index / (rows.length - 1)) * chartWidth);
  const y = (value: number) => top + chartHeight * (1 - value / ceiling);
  const path = rows
    .map(
      (row, index) =>
        `${index === 0 ? "M" : "L"}${x(index)},${y(row.sessions)}`,
    )
    .join(" ");
  const area = rows.length
    ? `${path} L${x(rows.length - 1)},${y(0)} L${x(0)},${y(0)} Z`
    : "";
  const labelIndices = [
    ...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1]),
  ];
  return (
    <>
      <svg
        className="trend-svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-labelledby={`${id}-title ${id}-desc`}
      >
        <title id={`${id}-title`}>Daily readership</title>
        <desc id={`${id}-desc`}>
          {rows.length} calendar days shown, including days with no sessions.
          Daily sessions range from{" "}
          {number(Math.min(...rows.map((row) => row.sessions)))} to{" "}
          {number(max)}. Open the data table below for exact daily counts.
        </desc>
        <defs>
          <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#456b56" stopOpacity=".16" />
            <stop offset="100%" stopColor="#456b56" stopOpacity=".01" />
          </linearGradient>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
          <g key={tick}>
            <line
              x1={left}
              x2={width - right}
              y1={y(ceiling * tick)}
              y2={y(ceiling * tick)}
              stroke="#e6e8e2"
              strokeDasharray={tick ? "3 5" : undefined}
            />
            <text x={left - 10} y={y(ceiling * tick) + 4} textAnchor="end">
              {number(ceiling * tick)}
            </text>
          </g>
        ))}
        <path d={area} fill={`url(#${id}-fill)`} />
        <path
          d={path}
          fill="none"
          stroke="#456b56"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
        {rows.map((row, index) => (
          <circle
            key={row.date}
            cx={x(index)}
            cy={y(row.sessions)}
            r={rows.length === 1 ? 4 : 3}
            className="chart-point"
          >
            <title>
              {dateLabel(row.date)}: {number(row.sessions)} sessions;{" "}
              {number(row.subscriptions)} subscriptions
            </title>
          </circle>
        ))}
        {labelIndices.map(
          (index) =>
            rows[index] && (
              <text
                key={index}
                x={x(index)}
                y={height - 8}
                textAnchor={
                  rows.length === 1
                    ? "middle"
                    : index === 0
                      ? "start"
                      : index === rows.length - 1
                        ? "end"
                        : "middle"
                }
              >
                {dateLabel(rows[index].date)}
              </text>
            ),
        )}
      </svg>
      <button
        className="text-button chart-table-toggle"
        aria-expanded={tableOpen}
        aria-controls={`${id}-table`}
        onClick={() => setTableOpen(!tableOpen)}
      >
        {tableOpen ? "Hide" : "View"} daily data{" "}
        <span aria-hidden="true">{tableOpen ? "−" : "+"}</span>
      </button>
      {tableOpen && (
        <div className="table-scroll daily-table" id={`${id}-table`}>
          <table>
            <caption className="sr-only">
              Daily session and subscription counts
            </caption>
            <thead>
              <tr>
                <th>Date</th>
                <th className="numeric">Sessions</th>
                <th className="numeric">Subscriptions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.date}>
                  <td>{dateLabel(row.date, true)}</td>
                  <td className="numeric">{number(row.sessions)}</td>
                  <td className="numeric">{number(row.subscriptions)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Metric({
  label,
  value,
  detail,
  accent = false,
}: {
  label: string;
  value: string;
  detail: string;
  accent?: boolean;
}) {
  return (
    <article className={`metric${accent ? " metric-accent" : ""}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

function Methodology() {
  return (
    <section
      id="methodology"
      className="methodology section-anchor"
      aria-labelledby="methodology-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Behind the analysis</p>
          <h2 id="methodology-heading">Every number has a definition.</h2>
        </div>
        <span className="section-index">03 / METHOD</span>
      </div>
      <div className="method-grid">
        <article>
          <span className="method-number">01</span>
          <h3>Start with trustworthy data</h3>
          <p>
            A deterministic Python pipeline validates session IDs, dates,
            category values and funnel consistency. Invalid records are
            quarantined, and duplicate sessions are removed before analysis.
          </p>
        </article>
        <article>
          <span className="method-number">02</span>
          <h3>Make the calculation explicit</h3>
          <p>
            An engaged session has at least 30 seconds of engaged time and 50%
            scroll depth. Engagement and conversion rates divide engaged or
            subscription sessions by all selected sessions. Average engaged time
            includes non-engaged visits. Rates are not averages of segment
            rates.
          </p>
        </article>
        <article>
          <span className="method-number">03</span>
          <h3>Turn patterns into questions</h3>
          <p>
            Compare channels and stories, then investigate why readers behave
            differently. These simulated observations support an analysis
            demonstration; they do not establish causal effects or publisher
            results.
          </p>
        </article>
      </div>
      <div className="method-note">
        <Icon name="file" />
        <p>
          <strong>Independent portfolio project.</strong> All reader activity
          and article examples are simulated. PressLens is not affiliated with
          The Economic Times. Dates reflect the demo dataset, not live traffic.
        </p>
      </div>
    </section>
  );
}

export default function App() {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [draft, setDraft] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);
  const [data, setData] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dateError, setDateError] = useState("");
  const [retry, setRetry] = useState(0);
  const [sort, setSort] = useState<
    "sessions" | "engagement_rate" | "subscriptions"
  >("sessions");
  const [articleCount, setArticleCount] = useState(8);

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setLoading(true);
    readJson<FilterOptions>("/api/v1/filters", controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setOptions(result);
        setDraft((current) =>
          current.start_date
            ? current
            : {
                ...EMPTY_FILTERS,
                start_date: result.date_min,
                end_date: result.date_max,
              },
        );
        setApplied((current) =>
          current.start_date
            ? current
            : {
                ...EMPTY_FILTERS,
                start_date: result.date_min,
                end_date: result.date_max,
              },
        );
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to connect to the analytics service.",
          );
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!options) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    readJson<Dashboard>(apiUrl("/api/v1/dashboard", applied), controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setData(result);
          setLoading(false);
          setArticleCount(8);
        }
      })
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load the selected data.",
          );
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [applied, options, retry]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const validation = validateDates(draft);
    setDateError(validation);
    if (!validation) setApplied({ ...draft });
  }
  function reset() {
    const all = {
      ...EMPTY_FILTERS,
      start_date: options?.date_min ?? "",
      end_date: options?.date_max ?? "",
    };
    setDraft(all);
    setApplied(all);
    setDateError("");
  }
  const update = (key: keyof Filters, value: string) => {
    setDraft((current) => ({ ...current, [key]: value }));
    setDateError("");
  };
  const summary = data?.summary;
  const articles = [...(data?.articles ?? [])].sort(
    (a, b) => b[sort] - a[sort] || a.title.localeCompare(b.title),
  );
  const channels = [...(data?.channels ?? [])].sort(
    (a, b) => b.sessions - a.sessions,
  );
  const maxChannel = Math.max(1, ...channels.map((item) => item.sessions));
  const periodStart = applied.start_date || options?.date_min;
  const periodEnd = applied.end_date || options?.date_max;
  const period =
    periodStart && periodEnd
      ? `${dateLabel(periodStart)} — ${dateLabel(periodEnd, true)}`
      : "All available dates";
  const activeSegments = [
    applied.category,
    applied.channel,
    applied.device,
  ].filter(Boolean);
  const changed = JSON.stringify(draft) !== JSON.stringify(applied);

  return (
    <div className="app-layout">
      <a className="skip-link" href="#main">
        Skip to analytics
      </a>
      <aside className="sidebar">
        <a className="brand" href="#overview" aria-label="PressLens overview">
          <span className="brand-mark">
            P<span>●</span>
          </span>
          <span>
            PressLens
            <span className="brand-subtitle">A clearer view of readership</span>
          </span>
        </a>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Dashboard sections">
          <a className="nav-link active" href="#overview">
            <Icon name="grid" />
            Overview
            <span className="nav-dot" />
          </a>
          <a className="nav-link" href="#editorial">
            <Icon name="chart" />
            Editorial performance
          </a>
          <a className="nav-link" href="#methodology">
            <Icon name="file" />
            Methodology
          </a>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-project">
            <span className="project-avatar">JA</span>
            <div>
              <strong>Jatin Aggarwal</strong>
              <span>Data analytics portfolio</span>
            </div>
          </div>
          <p>
            Built to ask better questions.
            <br />
            Designed to show the work.
          </p>
          <span className="sidebar-version">PRESSLENS / V0.1</span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            ANALYTICS WORKSPACE <span className="breadcrumb-slash">/</span>{" "}
            <strong>Audience overview</strong>
          </span>
          <span className="demo-badge">
            <span />
            Simulated publisher data
          </span>
        </header>
        <main id="main">
          <section
            id="overview"
            className="section-anchor"
            aria-labelledby="overview-heading"
          >
            <div className="page-heading">
              <div>
                <p className="eyebrow">Audience & newsroom analytics</p>
                <h1 id="overview-heading">
                  Read between the <em>numbers.</em>
                </h1>
                <p className="page-description">
                  Explore what readers choose, where they engage, and how visits
                  become subscriptions.
                </p>
              </div>
              <div className="edition">
                <span>THE READER’S EDITION</span>
                <strong>
                  01<span> / INSIGHTS</span>
                </strong>
              </div>
            </div>
            <form
              className="filter-panel"
              onSubmit={submit}
              aria-label="Filter analytics"
            >
              <div className="filter-heading">
                <span>
                  <Icon name="filter" />
                  Explore your audience
                </span>
                <button
                  className="text-button"
                  type="button"
                  onClick={reset}
                  disabled={!options}
                >
                  <Icon name="reset" size={14} />
                  Reset filters
                </button>
              </div>
              <div className="filter-fields">
                <label>
                  From
                  <input
                    type="date"
                    value={draft.start_date}
                    min={options?.date_min}
                    max={options?.date_max}
                    onChange={(event) =>
                      update("start_date", event.target.value)
                    }
                    disabled={!options}
                    aria-invalid={!!dateError}
                    aria-describedby={dateError ? "date-error" : undefined}
                  />
                </label>
                <label>
                  To
                  <input
                    type="date"
                    value={draft.end_date}
                    min={options?.date_min}
                    max={options?.date_max}
                    onChange={(event) => update("end_date", event.target.value)}
                    disabled={!options}
                    aria-invalid={!!dateError}
                  />
                </label>
                <label>
                  Category
                  <select
                    value={draft.category}
                    onChange={(event) => update("category", event.target.value)}
                    disabled={!options}
                  >
                    <option value="">All categories</option>
                    {options?.categories.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Channel
                  <select
                    value={draft.channel}
                    onChange={(event) => update("channel", event.target.value)}
                    disabled={!options}
                  >
                    <option value="">All channels</option>
                    {options?.channels.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Device
                  <select
                    value={draft.device}
                    onChange={(event) => update("device", event.target.value)}
                    disabled={!options}
                  >
                    <option value="">All devices</option>
                    {options?.devices.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <button
                  className="button button-primary apply-button"
                  type="submit"
                  disabled={!options || loading}
                >
                  Apply <Icon name="arrow" size={16} />
                </button>
              </div>
              {dateError && (
                <p className="form-error" id="date-error" role="alert">
                  {dateError}
                </p>
              )}
              {changed && !dateError && (
                <p className="filter-hint">
                  Apply filters to update the analysis.
                </p>
              )}
            </form>
            <div className="results-heading">
              <div>
                <span className="status-dot" />
                <strong>{period}</strong>
                <span className="result-scope">
                  {activeSegments.length
                    ? activeSegments.join(" · ")
                    : "All categories, channels & devices"}
                </span>
              </div>
              <button
                className="button button-export"
                disabled={!data || loading || !!error || !summary?.sessions}
                onClick={() => {
                  window.location.assign(apiUrl("/api/v1/export.csv", applied));
                }}
              >
                <Icon name="download" size={15} />
                Export CSV
              </button>
            </div>
            <div className="sr-only" role="status" aria-live="polite">
              {loading
                ? "Loading analytics."
                : error
                  ? "Analytics could not be loaded."
                  : `${number(summary?.sessions ?? 0)} sessions match the selected filters.`}
            </div>
            {error && (
              <div className="error-state" role="alert">
                <div>
                  <h2>We couldn’t load the analysis.</h2>
                  <p>{error}</p>
                  <p>
                    Check that the API is running and the demo dataset has been
                    built.
                  </p>
                </div>
                <button
                  className="button button-primary"
                  onClick={() => setRetry((value) => value + 1)}
                >
                  Try again <Icon name="reset" size={16} />
                </button>
              </div>
            )}
            {!data && loading && (
              <div className="loading-state" aria-hidden="true">
                <div className="skeleton-metrics">
                  {[0, 1, 2, 3].map((value) => (
                    <div className="skeleton" key={value} />
                  ))}
                </div>
                <div className="skeleton skeleton-chart" />
              </div>
            )}
            {data && !error && (
              <div
                className={loading ? "results results-loading" : "results"}
                aria-busy={loading}
              >
                <div className="metrics-grid">
                  <Metric
                    label="TOTAL SESSIONS"
                    value={number(data.summary.sessions)}
                    detail="Accepted visits in the selected period"
                  />
                  <Metric
                    label="ENGAGEMENT RATE"
                    value={percent(data.summary.engagement_rate)}
                    detail={`${number(data.summary.engaged_sessions)} engaged sessions`}
                    accent
                  />
                  <Metric
                    label="SUBSCRIPTIONS"
                    value={number(data.summary.subscriptions)}
                    detail={`${percent(data.summary.conversion_rate)} of sessions converted`}
                  />
                  <Metric
                    label="AVG. ENGAGED TIME"
                    value={duration(data.summary.avg_engaged_seconds)}
                    detail="Per session, including non-engaged visits"
                  />
                </div>
                {!data.summary.sessions ? (
                  <div className="empty-state">
                    <span className="empty-symbol">∅</span>
                    <h2>No sessions in this selection.</h2>
                    <p>
                      Try a wider date range or reset the category, channel and
                      device filters.
                    </p>
                    <button className="button button-primary" onClick={reset}>
                      Reset filters
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="charts-grid">
                      <section
                        className="panel trend-panel"
                        aria-labelledby="trend-heading"
                      >
                        <div className="panel-heading">
                          <div>
                            <p className="eyebrow">Readership over time</p>
                            <h2 id="trend-heading">The daily picture</h2>
                          </div>
                          <span className="chart-legend">
                            <span />
                            Sessions
                          </span>
                        </div>
                        <TrendChart
                          rows={data.daily}
                          startDate={
                            applied.start_date || options?.date_min || ""
                          }
                          endDate={applied.end_date || options?.date_max || ""}
                        />
                        <div className="chart-caption">
                          Daily sessions · {period}
                          <span>Selected audience</span>
                        </div>
                      </section>
                      <section
                        className="panel channels-panel"
                        aria-labelledby="channels-heading"
                      >
                        <div className="panel-heading">
                          <div>
                            <p className="eyebrow">Acquisition mix</p>
                            <h2 id="channels-heading">Where readers arrive</h2>
                          </div>
                          <Icon name="chart" />
                        </div>
                        <p className="panel-description">
                          Session volume and subscription conversion by channel.
                        </p>
                        <div className="channel-list">
                          {channels.map((item, index) => (
                            <div className="channel-row" key={item.channel}>
                              <div className="channel-label">
                                <span>
                                  <span className="channel-index">
                                    0{index + 1}
                                  </span>
                                  {item.channel}
                                </span>
                                <strong>{number(item.sessions)}</strong>
                              </div>
                              <svg
                                className="channel-bar"
                                viewBox="0 0 100 5"
                                preserveAspectRatio="none"
                                role="img"
                                aria-label={`${item.channel}: ${number(item.sessions)} sessions, ${percent(item.conversion_rate)} conversion`}
                              >
                                <rect
                                  className="channel-track"
                                  width="100"
                                  height="5"
                                  rx="2.5"
                                />
                                <rect
                                  className="channel-fill"
                                  width={(item.sessions / maxChannel) * 100}
                                  height="5"
                                  rx="2.5"
                                />
                              </svg>
                              <div className="channel-detail">
                                <span>
                                  {percent(item.engagement_rate)} engaged
                                </span>
                                <span>
                                  {percent(item.conversion_rate)} converted
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                        <p className="small-note">
                          Compare rates alongside sample sizes. Channel
                          differences are descriptive, not causal.
                        </p>
                      </section>
                    </div>
                    <section
                      id="editorial"
                      className="panel editorial-panel section-anchor"
                      aria-labelledby="editorial-heading"
                    >
                      <div className="panel-heading">
                        <div>
                          <p className="eyebrow">Editorial performance</p>
                          <h2 id="editorial-heading">
                            Stories that earn attention
                          </h2>
                        </div>
                        <label className="sort-control">
                          Sort by
                          <select
                            value={sort}
                            onChange={(event) =>
                              setSort(event.target.value as typeof sort)
                            }
                          >
                            <option value="sessions">Sessions</option>
                            <option value="engagement_rate">
                              Engagement rate
                            </option>
                            <option value="subscriptions">Subscriptions</option>
                          </select>
                        </label>
                      </div>
                      <div className="table-scroll">
                        <table>
                          <caption className="sr-only">
                            Article performance for the selected audience,
                            sorted by {sort.replace("_", " ")}
                          </caption>
                          <thead>
                            <tr>
                              <th className="rank-column">#</th>
                              <th>Article / category</th>
                              <th className="numeric">Sessions</th>
                              <th className="numeric">Engagement</th>
                              <th className="numeric">Subscriptions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {articles
                              .slice(0, articleCount)
                              .map((article, index) => (
                                <tr key={article.article_id}>
                                  <td className="rank-column">
                                    {String(index + 1).padStart(2, "0")}
                                  </td>
                                  <td>
                                    <span className="article-title">
                                      {article.title}
                                    </span>
                                    <span className="category-label">
                                      {article.category}
                                    </span>
                                  </td>
                                  <td className="numeric">
                                    {number(article.sessions)}
                                  </td>
                                  <td className="numeric">
                                    <span className="rate-cell">
                                      <svg
                                        className="mini-bar"
                                        viewBox="0 0 100 3"
                                        preserveAspectRatio="none"
                                        aria-hidden="true"
                                      >
                                        <rect
                                          className="mini-track"
                                          width="100"
                                          height="3"
                                          rx="1.5"
                                        />
                                        <rect
                                          className="mini-fill"
                                          width={Math.min(
                                            100,
                                            article.engagement_rate * 100,
                                          )}
                                          height="3"
                                          rx="1.5"
                                        />
                                      </svg>
                                      {percent(article.engagement_rate)}
                                    </span>
                                  </td>
                                  <td className="numeric">
                                    {number(article.subscriptions)}
                                  </td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="table-footer">
                        <span>
                          Showing {Math.min(articleCount, articles.length)} of{" "}
                          {articles.length} articles · Simulated article
                          examples
                        </span>
                        {articleCount < articles.length && (
                          <button
                            className="text-button"
                            onClick={() =>
                              setArticleCount((value) => value + 12)
                            }
                          >
                            Show more <Icon name="arrow" size={15} />
                          </button>
                        )}
                      </div>
                    </section>
                  </>
                )}
              </div>
            )}
          </section>
          <Methodology />
          <footer className="page-footer">
            <span>
              <strong>PressLens</strong>{" "}
              <span className="footer-divider">/</span> Audience & newsroom
              analytics
            </span>
            <span>Python · SQL · React · Reproducible analysis</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
