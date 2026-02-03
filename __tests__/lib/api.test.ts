import { fetchSignals, SignalResponse } from '@/lib/api';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Utilities', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('fetchSignals', () => {
        const API_URL = 'http://localhost:5000/api/kr/signals';

        it('successfully fetches signals data', async () => {
            const mockSignals: SignalResponse = {
                signals: [
                    {
                        ticker: '005930',
                        name: '삼성전자',
                        market: 'KOSPI',
                        current_price: 74200,
                        entry_price: 72000,
                        return_pct: 3.05,
                        status: 'OPEN',
                        score: 85,
                        theme: '반도체',
                    },
                ],
                count: 1,
            };

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => mockSignals,
            });

            const result = await fetchSignals();

            expect(result.signals).toHaveLength(1);
            expect(result.signals[0].ticker).toBe('005930');
            expect(result.signals[0].name).toBe('삼성전자');
        });

        it('throws error when fetch fails', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 500,
            });

            await expect(fetchSignals()).rejects.toThrow(`Failed to fetch ${API_URL}`);
        });

        it('calls correct API endpoint', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ signals: [], count: 0 }),
            });

            await fetchSignals();

            expect(global.fetch).toHaveBeenCalledWith(API_URL, expect.objectContaining({
                cache: 'no-store',
            }));
        });
    });
});
