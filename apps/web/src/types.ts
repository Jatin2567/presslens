export interface Filters {
  start_date: string;
  end_date: string;
  category: string;
  channel: string;
  device: string;
}

export interface FilterOptions {
  date_min: string;
  date_max: string;
  categories: string[];
  channels: string[];
  devices: string[];
}

export interface Dashboard {
  summary: {
    sessions: number;
    engaged_sessions: number;
    engagement_rate: number;
    subscriptions: number;
    conversion_rate: number;
    avg_engaged_seconds: number;
  };
  daily: { date: string; sessions: number; subscriptions: number }[];
  channels: {
    channel: string;
    sessions: number;
    engagement_rate: number;
    subscriptions: number;
    conversion_rate: number;
  }[];
  articles: {
    article_id: string;
    title: string;
    category: string;
    sessions: number;
    engagement_rate: number;
    subscriptions: number;
  }[];
  quality: Record<string, unknown>;
  meta: { simulated: boolean; [key: string]: unknown };
}
