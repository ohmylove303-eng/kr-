export interface Signal {
    ticker: string;
    name: string;
    market: string;
    current_price: number;
    entry_price: number;
    return_pct: number;
    status: string;
    score: number;
    final_score?: number;
    theme: string;
    contraction_ratio?: number;
    foreign_5d?: number;
    inst_5d?: number;
    nice_tech_score?: number;
    is_palantir?: boolean;
    is_palantir_mini?: boolean;

    // Nested backend data
    gpt_recommendation?: {
        action: string;
        confidence: number;
        reason: string;
    };
    gemini_recommendation?: {
        action: string;
        confidence: number;
        reason: string;
    };
    nice_layers?: {
        L1_technical: number;
        L2_supply: number;
        L3_sentiment: number;
        L4_macro: number;
        L5_institutional: number;
        total: number;
        max_total: number;
    };
    valuation?: {
        grade: string;
        description: string;
        per: string;
        pbr: string;
    };
    tp1?: number;
    tp2?: number;
    stop_loss?: number;
}

export interface MacroIndicators {
    exchange_rate: {
        rate: number;
        change_pct: number;
        risk_level: string;
    };
    interest_spread: {
        spread_bp: number;
        us_rate: number;
        kr_rate: number;
        capital_risk: string;
    };
    fx_reserves: {
        current_reserves: number;
        change: number;
        prev_reserves: number;
    };
    crisis: {
        crisis_score: number;
        crisis_level: string;
        message: string;
    };
}

export interface SectorPerformance {
    sectors: {
        name: string;
        change_pct: number;
        volume: number;
    }[];
}

export interface StockHistory {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface SignalResponse {
    signals: Signal[];
    count: number;
    generated_at?: string;
}

export interface MarketStatus {
    status: string;
    is_open: boolean;
    message: string;
}

export interface AIAnalysis {
    signal_date: string;
    market_analysis: string;
    sector_analysis: string;
    top_picks: any[];
    risk_assessment: string;
    overall_sentiment: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/kr';

// Helper to fetch data
async function fetchJson<T>(endpoint: string): Promise<T> {
    const res = await fetch(endpoint, {
        cache: "no-store",
    });

    if (!res.ok) {
        throw new Error(`Failed to fetch ${endpoint}`);
    }

    return res.json();
}

// Helper to post data
async function postJson<T>(endpoint: string, data: any): Promise<T> {
    const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        cache: 'no-store'
    });

    if (!res.ok) {
        throw new Error(`Failed to post to ${endpoint}`);
    }

    return res.json();
}

export const fetchSignals = () => fetchJson<SignalResponse>("/api/kr/signals");
export const fetchMarketStatus = () => fetchJson<MarketStatus>("/api/kr/market-status");
export const fetchAIAnalysis = () => fetchJson<AIAnalysis>("/api/kr/ai-analysis");
export const fetchMacroIndicators = () => fetchJson<MacroIndicators>("/api/kr/macro-indicators");
export const fetchSectorPerformance = () => fetchJson<SectorPerformance>("/api/kr/sector-performance");
export const fetchStockHistory = (ticker: string) => fetchJson<StockHistory[]>(`/api/kr/history/${ticker}?period=1y`);
export const fetchStockAnalysis = (ticker: string) => postJson<Signal>("/api/kr/analyze-stock", { ticker });
