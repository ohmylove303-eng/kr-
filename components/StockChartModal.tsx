"use client";

import { useEffect, useRef, useState } from "react";
import { Modal, Group, Stack, Text, Badge, Loader, Center, Grid, Divider, Button, Alert, Paper } from "@mantine/core";
import { IconReload, IconShieldCheck, IconSword, IconInfoCircle, IconRobot } from "@tabler/icons-react";
import { createChart, ColorType, IChartApi, CandlestickSeries } from "lightweight-charts";
import { fetchStockHistory, fetchStockAnalysis, Signal } from "@/lib/api";
import { NiceRadarChart } from "./NiceRadarChart";

interface StockChartModalProps {
    opened: boolean;
    onClose: () => void;
    signal: Signal | null;
}

export function StockChartModal({ opened, onClose, signal: initialSignal }: StockChartModalProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [loading, setLoading] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [signal, setSignal] = useState<Signal | null>(initialSignal);
    const [analysisResult, setAnalysisResult] = useState<{ source: string; action: string; reason: string } | null>(null);
    const [containerReady, setContainerReady] = useState(false);

    // Callback ref to detect when container is mounted
    const setChartContainerRef = (node: HTMLDivElement | null) => {
        chartContainerRef.current = node;
        if (node) {
            console.log('[StockChartModal] Container ref set, node clientWidth:', node.clientWidth);
            setContainerReady(true);
        } else {
            setContainerReady(false);
        }
    };

    // Sync prop to state when modal opens
    useEffect(() => {
        setSignal(initialSignal);
        setAnalysisResult(null);
        if (opened) setLoading(true); // Start loading immediately for smooth transition
    }, [initialSignal, opened]);

    const handleReAnalyze = async () => {
        if (!signal) return;
        try {
            setAnalyzing(true);
            setAnalysisResult(null);

            // Call Backend API
            const freshSignal = await fetchStockAnalysis(signal.ticker);

            // Merge fresh AI data into existing signal
            setSignal(prev => prev ? ({ ...prev, ...freshSignal }) : freshSignal);

            const rec = freshSignal.gpt_recommendation;
            const source = (rec as any).source || 'AI Model';

            // Update UI instead of Alert
            setAnalysisResult({
                source: source,
                action: rec?.action || 'HOLD',
                reason: rec?.reason || 'Analysis completed.'
            });

        } catch (e) {
            console.error(e);
            setError("Analysis failed. Please try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    useEffect(() => {
        console.log('[StockChartModal] useEffect triggered. opened:', opened, 'signal:', !!signal, 'containerReady:', containerReady);

        if (!opened || !signal || !containerReady || !chartContainerRef.current) {
            console.log('[StockChartModal] Early return - missing dependency');
            return;
        }

        console.log('[StockChartModal] All conditions met, proceeding with chart init');
        // Loading is already true from the effect above
        setError(null);

        // 1. Dispose previous chart if exists
        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        // Initial Chart Setup with Delay to allow Modal to render
        const initChart = setTimeout(() => {
            if (!chartContainerRef.current) return;

            // Dispose previous if any (double safety)
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }

            // Use fallback width if container doesn't have dimensions yet
            const containerWidth = chartContainerRef.current.clientWidth || 600;

            const chart = createChart(chartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: '#1A1A1A' },
                    textColor: '#D9D9D9',
                },
                grid: {
                    vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                    horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
                },
                width: containerWidth,
                height: 350,
            });

            chartRef.current = chart;

            // 3. Add Series using v5 API
            let candlestickSeries: any;
            try {
                candlestickSeries = chart.addSeries(CandlestickSeries, {
                    upColor: '#ef5350',      // Red for Up (KR Style)
                    downColor: '#26a69a',    // Blue/Green for Down
                    borderUpColor: '#ef5350',
                    wickUpColor: '#ef5350',
                    borderDownColor: '#26a69a',
                    wickDownColor: '#26a69a',
                });
            } catch (err) {
                console.error("Failed to add series:", err);
                setError("Chart initialization failed.");
                setLoading(false);
                return;
            }

            // 4. Fetch Data
            console.log('[StockChartModal] Fetching history for:', signal.ticker);
            fetchStockHistory(signal.ticker)
                .then((data) => {
                    console.log('[StockChartModal] History data received:', data?.length, 'records');
                    if (!data || data.length === 0) {
                        console.warn('[StockChartModal] No data received');
                        setLoading(false);
                        return;
                    }

                    const chartData = data.map(d => ({
                        time: d.date,
                        open: d.open,
                        high: d.high,
                        low: d.low,
                        close: d.close
                    }));

                    chartData.sort((a: any, b: any) => new Date(a.time).getTime() - new Date(b.time).getTime());

                    candlestickSeries.setData(chartData);
                    chart.timeScale().fitContent();
                })
                .catch((e) => {
                    console.error(e);
                    setError("Failed to load chart data");
                })
                .finally(() => {
                    setLoading(false);
                });
        }, 300); // 300ms delay for Modal transition

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            clearTimeout(initChart);
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        };
    }, [opened, signal?.ticker, containerReady]); // Re-run when container becomes ready

    if (!signal) return null;

    // Prepare Radar Data (Robust check)
    // Backend (On-Demand) now returns nested 'nice_layers', but existing signals might use flattened
    // We check both for robustness
    const layers = signal.nice_layers || (signal as any);

    const radarData = [
        { subject: 'Technical', A: layers.L1_technical || 0, fullMark: 100 },
        { subject: 'Supply', A: layers.L2_supply ? (layers.L2_supply * 3.3) : 0, fullMark: 100 },
        { subject: 'Sentiment', A: layers.L3_sentiment || 0, fullMark: 100 },
        { subject: 'Macro', A: layers.L4_macro ? (layers.L4_macro * 3) : 0, fullMark: 100 },
        { subject: 'Inst.', A: layers.L5_institutional ? (layers.L5_institutional * 3.5) : 0, fullMark: 100 },
    ];

    // Score calculation also handles both ways
    const totalScore = layers.total || layers.total_score || 0;
    const niceScore = totalScore ? Math.round((totalScore / 300) * 100) : 0;

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title={
                <Group>
                    <Text fw={700} size="lg">{signal.name}</Text>
                    <Text size="sm" c="dimmed">{signal.ticker}</Text>
                    <Badge color={signal.return_pct >= 0 ? "red" : "blue"} variant="light" size="lg">
                        {signal.return_pct > 0 ? "+" : ""}{signal.return_pct.toFixed(2)}%
                    </Badge>
                    {signal.is_palantir && <Badge color="grape" leftSection={<IconShieldCheck size={12} />}>PALANTIR</Badge>}
                    {signal.is_palantir_mini && <Badge color="orange" leftSection={<IconSword size={12} />}>MINI</Badge>}
                </Group>
            }
            size="80rem"
            centered
            styles={{
                content: { backgroundColor: '#1A1A1A', border: '1px solid rgba(255,255,255,0.1)' },
                header: { backgroundColor: '#1A1A1A', color: 'white' },
                body: { backgroundColor: '#1A1A1A', color: 'white' }
            }}
        >
            <Grid gutter="xl">
                {/* Left: Chart & AI Actions */}
                <Grid.Col span={{ base: 12, md: 8 }}>
                    <Stack>
                        <div style={{ position: 'relative' }}>
                            {loading && (
                                <Center style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 10, background: 'rgba(0,0,0,0.5)' }}>
                                    <Loader color="gray" />
                                </Center>
                            )}
                            <div ref={setChartContainerRef} style={{ width: '100%', height: 350 }} />
                        </div>

                        {error && <Text c="red" size="sm">{error}</Text>}

                        {/* AI Analysis Result Display */}
                        {analysisResult && (
                            <Alert
                                icon={<IconRobot size={16} />}
                                title={`AI Analysis: ${analysisResult.action}`}
                                color={analysisResult.action === 'BUY' ? 'teal' : analysisResult.action === 'SELL' ? 'red' : 'gray'}
                                variant="light"
                            >
                                <Text size="sm" mb="xs"><Text span fw={700}>[{analysisResult.source}]</Text> {analysisResult.reason}</Text>
                            </Alert>
                        )}

                        <Paper withBorder p="md" bg="rgba(255,255,255,0.05)" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                            <Group justify="space-between">
                                <Group>
                                    <Stack gap={0}>
                                        <Text size="xs" c="dimmed">GPT Opinion</Text>
                                        <Text fw={700} c="teal">{signal.gpt_recommendation?.action || "N/A"}</Text>
                                    </Stack>
                                    <Divider orientation="vertical" />
                                    <Stack gap={0}>
                                        <Text size="xs" c="dimmed">TP1 / TP2</Text>
                                        <Group gap={4}>
                                            <Text fw={700} c="red">₩{(signal.tp1 || 0).toLocaleString()}</Text>
                                            <Text size="xs" c="dimmed">/</Text>
                                            <Text fw={700} c="red">₩{(signal.tp2 || 0).toLocaleString()}</Text>
                                        </Group>
                                    </Stack>
                                </Group>

                                <Button
                                    leftSection={analyzing ? <Loader size="xs" color="white" /> : <IconReload size={14} />}
                                    variant="light"
                                    color="blue"
                                    loading={analyzing}
                                    onClick={handleReAnalyze}
                                >
                                    {analyzing ? "Thinking..." : "Re-Analyze"}
                                </Button>
                            </Group>
                        </Paper>
                    </Stack>
                </Grid.Col>

                {/* Right: NICE Model Report */}
                <Grid.Col span={{ base: 12, md: 4 }}>
                    <Stack gap="lg" h="100%" justify="flex-start" pt="md">
                        <Stack gap={0} align="center">
                            <Text fw={700} size="sm" ta="center" c="dimmed" tt="uppercase">NICE Model Analysis</Text>
                            <Text size="xs" c="dimmed">Quantitative Scoring System</Text>
                        </Stack>

                        {/* Radar Chart */}
                        <Center>
                            <NiceRadarChart data={radarData} score={niceScore} />
                        </Center>

                        <Divider color="white" opacity={0.1} />

                        {/* Detailed Metrics List */}
                        <Stack gap="sm">
                            <Group justify="space-between">
                                <Group gap="xs">
                                    <IconInfoCircle size={14} color="gray" />
                                    <Text size="sm" c="dimmed">VCP Contraction</Text>
                                </Group>
                                <Text size="sm" fw={700}>{signal.contraction_ratio ? signal.contraction_ratio.toFixed(2) : '-'} (Target &lt; 0.85)</Text>
                            </Group>
                            <Group justify="space-between">
                                <Group gap="xs">
                                    <IconInfoCircle size={14} color="gray" />
                                    <Text size="sm" c="dimmed">Foreign (5D)</Text>
                                </Group>
                                <Text size="sm" fw={700} c={(signal.foreign_5d || 0) > 0 ? "red" : "blue"}>
                                    {(signal.foreign_5d || 0).toLocaleString()}
                                </Text>
                            </Group>
                            <Group justify="space-between">
                                <Group gap="xs">
                                    <IconInfoCircle size={14} color="gray" />
                                    <Text size="sm" c="dimmed">Inst. (5D)</Text>
                                </Group>
                                <Text size="sm" fw={700} c={(signal.inst_5d || 0) > 0 ? "red" : "blue"}>
                                    {(signal.inst_5d || 0).toLocaleString()}
                                </Text>
                            </Group>
                        </Stack>
                    </Stack>
                </Grid.Col>
            </Grid>
        </Modal>
    );
}
