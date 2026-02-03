"use client";

import { Container, SimpleGrid, Group, Stack, Badge, Text, Button, Loader, Center, Table, Progress, ActionIcon, Tooltip, Paper } from "@mantine/core";
import { IconRocket, IconTarget, IconAlertTriangle, IconRefresh, IconChartLine, IconInfoCircle, IconClock, IconCategory, IconHome } from "@tabler/icons-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { PageTitle } from "@/components/ui/PageTitle";
import { StockChartModal } from "@/components/StockChartModal";
import useSWR from "swr";
import { useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5001";

// Types
interface JonggaSignal {
    stock_code: string;
    stock_name: string;
    market: string;
    grade: string;
    score: {
        total: number;
        news: number;
        volume: number;
        chart: number;
        candle: number;
        consolidation: number;
        supply: number;
        llm_reason: string;
    };
    current_price: number;
    entry_price: number;
    stop_price: number;
    target_price: number;
    change_pct: number;
    trading_value: number;
    foreign_5d: number;
    inst_5d: number;
    news_items: Array<{ title: string; source: string; url: string }>;
    signal_date: string;
}

interface JonggaData {
    signals: JonggaSignal[];
    date: string;
    processing_time_ms: number;
    updated_at: string;
}

interface StatusData {
    status: string;
    last_updated: string;
    signals_count: number;
    by_grade: Record<string, number>;
}

// Fetcher
const fetcher = (url: string) => fetch(API_BASE + url).then(res => res.json());

// Grade badge colors
const gradeColors: Record<string, string> = {
    S: 'pink',
    A: 'violet',
    B: 'blue',
    C: 'gray'
};

// Format number (억 단위)
const formatValue = (value: number): string => {
    if (value >= 100000000000) return `${(value / 1000000000000).toFixed(1)}조`;
    if (value >= 100000000) return `${(value / 100000000).toFixed(0)}억`;
    if (value >= 10000) return `${(value / 10000).toFixed(0)}만`;
    return value.toLocaleString();
};

export default function ClosingPage() {
    const [selectedSignal, setSelectedSignal] = useState<JonggaSignal | null>(null);
    const [chartOpened, setChartOpened] = useState(false);
    const [isRunning, setIsRunning] = useState(false);

    // Data fetching
    const { data, error, isLoading, mutate } = useSWR<JonggaData>('/api/kr/jongga-v2', fetcher, {
        refreshInterval: 1000 * 60 * 5
    });

    const { data: statusData } = useSWR<StatusData>('/api/kr/jongga-v2/status', fetcher, {
        refreshInterval: 1000 * 60
    });

    // Run screener
    const runScreener = async () => {
        setIsRunning(true);
        try {
            const res = await fetch(`${API_BASE}/api/kr/jongga-v2/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ capital: 50000000 })
            });
            if (res.ok) {
                mutate(); // Refresh data
            }
        } catch (e) {
            console.error('Screener error:', e);
        } finally {
            setIsRunning(false);
        }
    };

    const handleSignalClick = (signal: JonggaSignal) => {
        setSelectedSignal(signal);
        setChartOpened(true);
    };

    if (error) return (
        <Center h="100vh" className="bg-black text-white">
            <Stack align="center">
                <IconAlertTriangle size={48} className="text-red-500" />
                <Text fw={700} size="xl">Connection Error</Text>
                <Text c="dimmed">Failed to load Jongga V2 signals.</Text>
                <Button variant="light" color="gray" onClick={() => window.location.reload()}>Retry</Button>
            </Stack>
        </Center>
    );

    const signals = data?.signals || [];
    const gradeStats = statusData?.by_grade || {};

    return (
        <main className="min-h-screen bg-black pb-20">
            {/* Floating Navigation Dock */}
            <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50">
                <div className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-xl rounded-full border border-white/20 shadow-2xl">
                    <Link href="/">
                        <Button variant="subtle" color="gray" size="xs" radius="xl" leftSection={<IconHome size={14} />}>
                            홈
                        </Button>
                    </Link>
                    <Button variant="filled" color="violet" size="xs" radius="xl" leftSection={<IconClock size={14} />}>
                        종가베팅
                    </Button>
                    <Link href="/themes">
                        <Button variant="light" color="teal" size="xs" radius="xl" leftSection={<IconCategory size={14} />}>
                            테마분석
                        </Button>
                    </Link>
                </div>
            </div>
            <Container size="xl" pt={120}>
                <PageTitle
                    title="종가베팅 V2"
                    subtitle="AI-Powered Closing Bet Signal System"
                />

                {/* Status Cards */}
                <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg" mb={30}>
                    {/* Total Signals */}
                    <GlassCard p="lg" delay={0.1}>
                        <Group justify="space-between" align="start">
                            <Stack gap={4}>
                                <Text c="dimmed" size="xs" fw={700} tt="uppercase">Total Signals</Text>
                                <Text size="2rem" fw={800}>{signals.length}</Text>
                            </Stack>
                            <IconRocket size={24} className="text-purple-400" />
                        </Group>
                    </GlassCard>

                    {/* S Grade */}
                    <GlassCard p="lg" delay={0.15}>
                        <Group justify="space-between" align="start">
                            <Stack gap={4}>
                                <Badge color="pink" variant="light">S Grade</Badge>
                                <Text size="2rem" fw={800}>{gradeStats['S'] || 0}</Text>
                            </Stack>
                            <IconTarget size={24} className="text-pink-400" />
                        </Group>
                    </GlassCard>

                    {/* A Grade */}
                    <GlassCard p="lg" delay={0.2}>
                        <Group justify="space-between" align="start">
                            <Stack gap={4}>
                                <Badge color="violet" variant="light">A Grade</Badge>
                                <Text size="2rem" fw={800}>{gradeStats['A'] || 0}</Text>
                            </Stack>
                            <IconChartLine size={24} className="text-violet-400" />
                        </Group>
                    </GlassCard>

                    {/* Last Updated */}
                    <GlassCard p="lg" delay={0.25}>
                        <Group justify="space-between" align="start">
                            <Stack gap={4}>
                                <Text c="dimmed" size="xs" fw={700} tt="uppercase">Updated</Text>
                                <Text size="sm" fw={600}>
                                    {statusData?.last_updated ? new Date(statusData.last_updated).toLocaleTimeString('ko-KR') : '-'}
                                </Text>
                            </Stack>
                            <Tooltip label="Run Screener">
                                <ActionIcon
                                    variant="light"
                                    color="blue"
                                    size="lg"
                                    loading={isRunning}
                                    onClick={runScreener}
                                >
                                    <IconRefresh size={18} />
                                </ActionIcon>
                            </Tooltip>
                        </Group>
                    </GlassCard>
                </SimpleGrid>

                {/* Signals Table */}
                <GlassCard p={0} delay={0.3}>
                    <div className="p-6 border-b border-white/10">
                        <Group justify="space-between">
                            <Group>
                                <Text size="lg" fw={700}>Today's Signals</Text>
                                <Badge color="gray" variant="light">{data?.date || '-'}</Badge>
                            </Group>
                            <Button
                                variant="gradient"
                                gradient={{ from: 'violet', to: 'pink' }}
                                size="xs"
                                radius="xl"
                                loading={isRunning}
                                onClick={runScreener}
                            >
                                {isRunning ? 'Scanning...' : 'Run Screener'}
                            </Button>
                        </Group>
                    </div>

                    <div className="p-4 overflow-x-auto">
                        {isLoading ? (
                            <Center py={50}><Loader color="white" /></Center>
                        ) : signals.length === 0 ? (
                            <Center py={50}>
                                <Stack align="center">
                                    <IconInfoCircle size={40} className="text-gray-500" />
                                    <Text c="dimmed">No signals available. Run the screener to generate signals.</Text>
                                </Stack>
                            </Center>
                        ) : (
                            <Table horizontalSpacing="md" verticalSpacing="sm" striped highlightOnHover>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Grade</Table.Th>
                                        <Table.Th>Code</Table.Th>
                                        <Table.Th>Name</Table.Th>
                                        <Table.Th>Market</Table.Th>
                                        <Table.Th style={{ textAlign: 'right' }}>Price</Table.Th>
                                        <Table.Th style={{ textAlign: 'right' }}>Change</Table.Th>
                                        <Table.Th style={{ textAlign: 'right' }}>Score</Table.Th>
                                        <Table.Th style={{ textAlign: 'right' }}>Trading</Table.Th>
                                        <Table.Th>Supply</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {signals.map((signal, idx) => (
                                        <Table.Tr
                                            key={signal.stock_code}
                                            onClick={() => handleSignalClick(signal)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <Table.Td>
                                                <Badge color={gradeColors[signal.grade] || 'gray'} variant="filled" size="lg">
                                                    {signal.grade}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text fw={600} ff="monospace">{signal.stock_code}</Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text fw={600} truncate style={{ maxWidth: 150 }}>{signal.stock_name}</Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Badge color={signal.market === 'KOSPI' ? 'blue' : 'teal'} variant="light" size="sm">
                                                    {signal.market}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td style={{ textAlign: 'right' }}>
                                                <Text fw={700}>{signal.current_price.toLocaleString()}원</Text>
                                            </Table.Td>
                                            <Table.Td style={{ textAlign: 'right' }}>
                                                <Text
                                                    fw={700}
                                                    c={signal.change_pct > 0 ? 'red' : signal.change_pct < 0 ? 'blue' : 'gray'}
                                                >
                                                    {signal.change_pct > 0 ? '+' : ''}{signal.change_pct.toFixed(2)}%
                                                </Text>
                                            </Table.Td>
                                            <Table.Td style={{ textAlign: 'right' }}>
                                                <Group gap={4} justify="flex-end">
                                                    <Text fw={700}>{signal.score.total}/12</Text>
                                                    <Progress
                                                        value={(signal.score.total / 12) * 100}
                                                        size="sm"
                                                        w={50}
                                                        color={signal.score.total >= 10 ? 'pink' : signal.score.total >= 8 ? 'violet' : 'blue'}
                                                    />
                                                </Group>
                                            </Table.Td>
                                            <Table.Td style={{ textAlign: 'right' }}>
                                                <Text size="sm">{formatValue(signal.trading_value)}</Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Group gap={4}>
                                                    {signal.foreign_5d > 0 ? (
                                                        <Badge color="red" variant="light" size="xs">외+</Badge>
                                                    ) : signal.foreign_5d < 0 ? (
                                                        <Badge color="blue" variant="light" size="xs">외-</Badge>
                                                    ) : null}
                                                    {signal.inst_5d > 0 ? (
                                                        <Badge color="red" variant="light" size="xs">기+</Badge>
                                                    ) : signal.inst_5d < 0 ? (
                                                        <Badge color="blue" variant="light" size="xs">기-</Badge>
                                                    ) : null}
                                                </Group>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        )}
                    </div>
                </GlassCard>

                {/* Score Legend */}
                <Paper bg="transparent" p="md" mt="lg">
                    <Text size="xs" c="dimmed" mb="xs">Score Components: News(3) + Volume(3) + Chart(2) + Candle(1) + Consolidation(1) + Supply(2) = 12 Max</Text>
                    <Group gap="lg">
                        <Badge color="pink">S: 10+ & 1조+</Badge>
                        <Badge color="violet">A: 8+ & 5천억+</Badge>
                        <Badge color="blue">B: 6+ & 1천억+</Badge>
                        <Badge color="gray">C: Others</Badge>
                    </Group>
                </Paper>

            </Container>

            {/* Chart Modal - Reuse existing component */}
            {selectedSignal && (
                <StockChartModal
                    opened={chartOpened}
                    onClose={() => setChartOpened(false)}
                    signal={{
                        ticker: selectedSignal.stock_code,
                        name: selectedSignal.stock_name,
                        market: selectedSignal.market,
                        current_price: selectedSignal.current_price,
                        score: selectedSignal.score.total,
                        entry_price: selectedSignal.entry_price,
                        return_pct: 0,
                        status: 'JONGGA',
                        theme: selectedSignal.grade
                    }}
                />
            )}
        </main>
    );
}
