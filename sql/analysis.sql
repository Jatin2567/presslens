-- PressLens analysis examples. Run against data/demo/presslens.sqlite.
-- All source observations are fictional. Rates are per session, not per reader.

-- Channel contribution and conversion, with an explicit denominator.
SELECT channel,
       COUNT(*) AS sessions,
       SUM(engaged) AS engaged_sessions,
       ROUND(100.0 * SUM(engaged) / COUNT(*), 2) AS engagement_pct,
       SUM(subscribed) AS subscriptions,
       ROUND(100.0 * SUM(subscribed) / COUNT(*), 2) AS conversion_pct,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS traffic_share_pct
FROM fact_session
GROUP BY channel
ORDER BY conversion_pct DESC;

-- Editorial ranking: compare articles within their category using a window function.
-- A minimum denominator avoids making rankings from tiny groups.
WITH article_performance AS (
    SELECT a.article_id, a.title, a.category, COUNT(*) AS sessions,
           1.0 * SUM(s.engaged) / COUNT(*) AS engagement_rate,
           SUM(s.subscribed) AS subscriptions
    FROM fact_session s
    JOIN dim_article a USING (article_id)
    GROUP BY a.article_id, a.title, a.category
    HAVING COUNT(*) >= 100
)
SELECT *, DENSE_RANK() OVER (
    PARTITION BY category ORDER BY engagement_rate DESC
) AS category_rank
FROM article_performance
ORDER BY category, category_rank;

-- Seven calendar-day average. A calendar spine preserves dates with no sessions.
WITH RECURSIVE calendar(date) AS (
    SELECT MIN(date) FROM fact_session
    UNION ALL
    SELECT DATE(date, '+1 day') FROM calendar
    WHERE date < (SELECT MAX(date) FROM fact_session)
), daily AS (
    SELECT calendar.date, COUNT(s.session_id) AS sessions,
           COALESCE(SUM(s.subscribed), 0) AS subscriptions
    FROM calendar LEFT JOIN fact_session s ON s.date = calendar.date
    GROUP BY calendar.date
)
SELECT date, sessions, subscriptions,
       ROUND(AVG(sessions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
           AS trailing_7_day_sessions
FROM daily
ORDER BY date;

-- Reconciliation: each of these should return zero mismatches.
SELECT COUNT(*) AS orphan_sessions FROM fact_session s
LEFT JOIN dim_article a USING (article_id) WHERE a.article_id IS NULL;
SELECT COUNT(*) AS invalid_funnel_rows FROM fact_session
WHERE subscribed > engaged OR newsletter_signup > engaged;
