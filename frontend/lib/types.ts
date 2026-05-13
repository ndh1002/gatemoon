export type ScanPayload = {
  type: string;
  generated_at?: string | null;
  count?: number;
  rows?: ScanRow[];
};

export type VolumeLeader = {
  market?: string;
  quote_volume?: number;
  moonshot_score?: number;
  risk_score?: number;
  ts?: string;
};

export type SmartMoneyRow = {
  symbol?: string;
  smart_money?: number;
  whale_activity?: number;
  moonshot_score?: number;
  risk_score?: number;
  confidence?: number;
  ts?: string;
};

export type RiskAnalysisRow = {
  symbol?: string;
  risk_score?: number;
  moonshot_score?: number;
  confidence?: number;
  spread_risk?: number;
  volatility_risk?: number;
  ts?: string;
};

export type AlertRow = {
  id: number;
  market: string;
  channel: string;
  status: string;
  payload: string;
  ts?: string | null;
};

export type ScanRow = {
  symbol: string;
  ticker: {
    symbol?: string;
    last?: number;
    quoteVolume?: number;
    baseVolume?: number;
    percentage?: number;
    bid?: number;
    ask?: number;
    high?: number;
    low?: number;
  };
  moonshot_score: number;
  confidence: number;
  risk_score: number;
  details: Record<string, unknown>;
  ts?: string;
};
