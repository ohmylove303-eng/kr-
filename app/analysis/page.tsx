"use client";

import { Container, Stack, Text, Loader, Badge, SimpleGrid } from "@mantine/core";
import { PageTitle } from "@/components/ui/PageTitle";
import { GlassCard } from "@/components/ui/GlassCard";
import { MacroDashboard } from "@/components/MacroDashboard";
import useSWR from "swr";
import { fetchAIAnalysis } from "@/lib/api";

export default function AnalysisPage() {
    const { data: aiData, isLoading: aiLoading } = useSWR('/api/kr/ai-analysis', fetchAIAnalysis);

    return (
        <main className="min-h-screen bg-black pb-20">
            <Container size="xl" pt={120}>
                <PageTitle
                    title="Market Analysis"
                    subtitle="Macroeconomic Indicators & AI Insights"
                />

                {/* 1. Macro Dashboard */}
                <Stack mb={40}>
                    <Text fw={700} c="dimmed" size="sm">MACROECONOMIC INDICATORS</Text>
                    <MacroDashboard />
                </Stack>

                {/* 2. Detailed AI Analysis */}
                <Stack>
                    <Text fw={700} c="dimmed" size="sm">AI MARKET COMMENTARY</Text>
                    <GlassCard p="xl">
                        {aiLoading ? (
                            <Loader color="white" />
                        ) : aiData ? (
                            <Stack gap="lg">
                                <SimpleGrid cols={{ base: 1, md: 2 }}>
                                    <div>
                                        <Text size="lg" fw={700} mb="xs">Market Sentiment</Text>
                                        <Badge
                                            size="xl"
                                            variant="gradient"
                                            gradient={aiData.overall_sentiment?.includes('Positive') ? { from: 'teal', to: 'lime', deg: 90 } : { from: 'orange', to: 'red', deg: 90 }}
                                        >
                                            {aiData.overall_sentiment || "NEUTRAL"}
                                        </Badge>
                                    </div>
                                    <div>
                                        <Text size="lg" fw={700} mb="xs">Key Drivers</Text>
                                        <Text c="dimmed" size="sm">
                                            Analysis based on KOSPI/KOSDAQ trends, exchange rates, and sector performance.
                                        </Text>
                                    </div>
                                </SimpleGrid>

                                <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                                    <Text size="md" style={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                                        {aiData.market_analysis}
                                    </Text>
                                </div>
                            </Stack>
                        ) : (
                            <Text c="dimmed">No Analysis Available</Text>
                        )}
                    </GlassCard>
                </Stack>
            </Container>
        </main>
    );
}
