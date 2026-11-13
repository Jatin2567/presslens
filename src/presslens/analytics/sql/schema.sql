PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE dim_article (
    article_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL
) STRICT;

CREATE TABLE fact_session (
    session_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    article_id TEXT NOT NULL REFERENCES dim_article(article_id),
    channel TEXT NOT NULL CHECK (channel IN ('Search','Direct','Social','Newsletter','Referral')),
    device TEXT NOT NULL CHECK (device IN ('Desktop','Mobile','Tablet')),
    engaged_seconds INTEGER NOT NULL CHECK (engaged_seconds BETWEEN 0 AND 3600),
    scroll_depth INTEGER NOT NULL CHECK (scroll_depth BETWEEN 0 AND 100),
    engaged INTEGER NOT NULL CHECK (engaged IN (0,1)),
    newsletter_signup INTEGER NOT NULL CHECK (newsletter_signup IN (0,1)),
    subscribed INTEGER NOT NULL CHECK (subscribed IN (0,1)),
    CHECK (engaged = CASE WHEN engaged_seconds >= 30 AND scroll_depth >= 50 THEN 1 ELSE 0 END),
    CHECK (subscribed <= engaged),
    CHECK (newsletter_signup <= engaged)
) STRICT;

CREATE INDEX idx_session_date ON fact_session(date);
CREATE INDEX idx_session_channel_date ON fact_session(channel, date);
CREATE INDEX idx_session_article ON fact_session(article_id);
CREATE INDEX idx_article_category ON dim_article(category);

CREATE TABLE snapshot_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT;

CREATE VIEW mart_daily AS
SELECT date, COUNT(*) AS sessions, SUM(engaged) AS engaged_sessions,
       SUM(subscribed) AS subscriptions,
       ROUND(1.0 * SUM(engaged) / COUNT(*), 6) AS engagement_rate,
       ROUND(1.0 * SUM(subscribed) / COUNT(*), 6) AS conversion_rate
FROM fact_session GROUP BY date;

CREATE VIEW mart_article AS
SELECT a.article_id, a.title, a.category, COUNT(*) AS sessions,
       SUM(s.engaged) AS engaged_sessions, SUM(s.subscribed) AS subscriptions
FROM fact_session s JOIN dim_article a USING (article_id)
GROUP BY a.article_id, a.title, a.category;
