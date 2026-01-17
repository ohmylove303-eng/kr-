"use client";

import { Container, SimpleGrid, Group, Stack, Badge, Text, Button, Loader, Center } from "@mantine/core";
import { IconCpu, IconChartLine, IconTrendingUp, IconBolt, IconSearch, IconAlertTriangle } from "@tabler/icons-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { PageTitle } from "@/components/ui/PageTitle";
import { SignalTable } from "@/components/SignalTable";
import { MacroDashboard } from "@/components/MacroDashboard";
import { SectorGrid } from "@/components/SectorGrid";
import { StockChartModal } from "@/components/StockChartModal";
import useSWR from "swr";
import { fetchSignals, fetchMarketStatus, fetchAIAnalysis, Signal } from "@/lib/api";
import { useState } from "react";

export default function Home() {
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [chartOpened, setChartOpened] = useState(false);

  // Data Fetching
  const { data: signalData, error: signalError, isLoading: signalLoading } = useSWR('/api/kr/signals', fetchSignals, {
    refreshInterval: 1000 * 60 * 5 // 5 minutes
  });

  const { data: marketData, isLoading: marketLoading } = useSWR('/api/kr/market-status', fetchMarketStatus, {
    refreshInterval: 1000 * 60 // 1 minute
  });

  const { data: aiData, isLoading: aiLoading } = useSWR('/api/kr/ai-analysis', fetchAIAnalysis, {
    revalidateOnFocus: false
  });

  const handleSignalClick = (signal: Signal) => {
    setSelectedSignal(signal);
    setChartOpened(true);
  };

  if (signalError) return (
    <Center h="100vh" className="bg-black text-white">
      <Stack align="center">
        <IconAlertTriangle size={48} className="text-red-500" />
        <Text fw={700} size="xl">Connection Lost</Text>
        <Text c="dimmed">Failed to connect to the market server.</Text>
        <Button variant="light" color="gray" onClick={() => window.location.reload()}>Retry</Button>
      </Stack>
    </Center>
  );

  const signals = signalData?.signals || [];
  // Sort by final_score if available, otherwise score
  const sortedSignals = [...signals].sort((a, b) => (b.final_score || b.score) - (a.final_score || a.score));
  const topSignal = sortedSignals.length > 0 ? sortedSignals[0] : null;

  const isMarketOpen = marketData?.is_open ?? false;
  const marketStatusMsg = marketData?.message || "Check Status";

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Floating Header / Dock Island */}

      <Container size="xl" pt={120}>
        <PageTitle
          title="Market Intelligence"
          subtitle="AI-Driven Analysis for Korean Stocks"
        />

        {/* 1. Macro Economic Indicators (Restored) */}
        <MacroDashboard />

        {/* Hero Status Section */}
        <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg" mb={30}>
          {/* Market Status Card */}
          <GlassCard p="xl" className="flex flex-col justify-between h-[200px]" delay={0.1}>
            <Group justify="space-between" align="start">
              <Stack gap={4}>
                <Text c="dimmed" size="xs" fw={700} tt="uppercase">Market Status</Text>
                {marketLoading ? <Loader size="sm" color="gray" /> : (
                  <Badge
                    size="lg"
                    variant="gradient"
                    gradient={isMarketOpen ? { from: 'teal', to: 'lime', deg: 90 } : { from: 'orange', to: 'red', deg: 90 }}
                  >
                    {isMarketOpen ? 'MARKET OPEN' : 'MARKET CLOSED'}
                  </Badge>
                )}
              </Stack>
              <IconBolt size={24} className={isMarketOpen ? "text-yellow-400" : "text-gray-500"} />
            </Group>
            <div>
              <Text size="3rem" fw={800} style={{ letterSpacing: '-2px', lineHeight: 1 }}>
                KOSPI
              </Text>
              <Text c="dimmed" fw={600} size="sm">{marketStatusMsg}</Text>
            </div>
          </GlassCard>

          {/* AI Signal Summary */}
          <GlassCard p="xl" className="flex flex-col justify-between h-[200px]" delay={0.2}>
            <Group justify="space-between" align="start">
              <Stack gap={4}>
                <Text c="dimmed" size="xs" fw={700} tt="uppercase">AI Signals</Text>
                <Text size="xl" fw={700}>Today's Picks</Text>
              </Stack>
              <IconCpu size={24} className="text-blue-400" />
            </Group>
            <Group align="end" gap="xs">
              {signalLoading ? <Loader color="white" type="dots" /> : (
                <Text size="3rem" fw={800} style={{ letterSpacing: '-2px', lineHeight: 1 }}>
                  {signals.length}
                </Text>
              )}
              <Text c="dimmed" mb={6}>Active Signals</Text>
            </Group>
          </GlassCard>

          {/* Top Sector / Theme */}
          <GlassCard p="xl" className="flex flex-col justify-between h-[200px]" delay={0.3}>
            <Group justify="space-between" align="start">
              <Stack gap={4}>
                <Text c="dimmed" size="xs" fw={700} tt="uppercase">Top Pick</Text>
                <Text size="xl" fw={700} truncate>{topSignal?.name || "Analyzing..."}</Text>
              </Stack>
              <IconTrendingUp size={24} className="text-red-400" />
            </Group>

            {/* Mini Chart Visual (SVG proxy) */}
            <div className="h-16 w-full flex items-end gap-1 opacity-50">
              {[40, 60, 45, 70, 85, 65, 90, 100].map((h, i) => (
                <div key={i} className="flex-1 bg-white rounded-t-sm" style={{ height: `${h}%` }} />
              ))}
            </div>
          </GlassCard>
        </SimpleGrid>

        {/* 2. Sector Performance Grid (Restored) */}
        <Text fw={700} c="dimmed" mb="xs" size="sm">SECTOR PERFORMANCE</Text>
        <div className="mb-8">
          <SectorGrid />
        </div>

        {/* Main Content Grid (Bento) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Main Signals List */}
          <div className="lg:col-span-2">
            <GlassCard p={0} delay={0.4} className="min-h-[500px]">
              <div className="p-6 border-b border-white/10">
                <Group justify="space-between">
                  <Text size="lg" fw={700}>Real-time VCP Signals</Text>
                  <Button variant="light" color="gray" size="xs" radius="xl">View All</Button>
                </Group>
              </div>
              {/* Signal List */}
              <div className="p-6 overflow-x-auto">
                {signalLoading ? (
                  <Center py={50}><Loader color="white" /></Center>
                ) : (
                  <SignalTable
                    signals={sortedSignals.slice(0, 20)}
                    onRowClick={handleSignalClick}
                  />
                )}
              </div>
            </GlassCard>
          </div>

          {/* Right: AI Analysis & Feed */}
          <div className="flex flex-col gap-6">
            <GlassCard p="xl" delay={0.5} className="flex-1">
              <Text size="lg" fw={700} mb="md">AI Commentary</Text>
              <Stack gap="sm">
                {aiLoading ? (
                  <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-white/10 rounded w-3/4"></div>
                    <div className="h-4 bg-white/10 rounded w-1/2"></div>
                  </div>
                ) : aiData ? (
                  <div className="p-3 rounded-lg bg-white/5 text-sm leading-relaxed text-gray-300">
                    {/* Show Market Analysis snippet if available */}
                    <Text size="sm" fw={600} c="white" mb={2}>Market Analysis</Text>
                    <Text size="sm" lineClamp={6} style={{ whiteSpace: 'pre-line' }}>{aiData.market_analysis || "No commentary available."}</Text>

                    {aiData.overall_sentiment && (
                      <Badge mt="xs" color={aiData.overall_sentiment.includes('Positive') || aiData.overall_sentiment.includes('Bullish') ? 'teal' : 'gray'}>
                        {aiData.overall_sentiment}
                      </Badge>
                    )}
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-white/5 text-sm leading-relaxed text-gray-300">
                    "AI Analysis data is currently unavailable. Please ensure the backend analyzer has run."
                  </div>
                )}
              </Stack>
            </GlassCard>

            <GlassCard p="xl" delay={0.6} className="h-[200px] bg-gradient-to-br from-blue-900/50 to-purple-900/50">
              <Stack justify="center" h="100%" align="center">
                <IconChartLine size={40} className="text-white/80" />
                <Text fw={700}>Portfolio Analytics</Text>
                <Button variant="white" color="dark" radius="xl" size="xs">Analyze Now</Button>
              </Stack>
            </GlassCard>
          </div>
        </div>

      </Container>

      {/* 3. Stock Chart Modal (Restored) */}
      <StockChartModal
        opened={chartOpened}
        onClose={() => setChartOpened(false)}
        signal={selectedSignal}
      />
    </main>
  );
}
