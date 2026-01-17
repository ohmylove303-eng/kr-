"use client";

import { Grid, Paper, Text, Group, Stack, RingProgress, Center, ThemeIcon, Loader } from "@mantine/core";
import { IconCurrencyDollar, IconChartBar, IconAlertTriangle, IconWorld } from "@tabler/icons-react";
import useSWR from "swr";
import { fetchMacroIndicators } from "@/lib/api";

export function MacroDashboard() {
    const { data, error, isLoading } = useSWR("macro-indicators", fetchMacroIndicators, { refreshInterval: 60000 });

    if (isLoading) return <Loader size="sm" color="gray" />;
    if (error || !data) return null;

    const { exchange_rate, interest_spread, fx_reserves, crisis } = data;

    // Crisis Ring Color
    const getCrisisColor = (level: string) => {
        switch (level) {
            case "critical": return "red";
            case "warning": return "orange";
            case "elevated": return "yellow";
            default: return "teal";
        }
    };

    return (
        <Grid gutter="md" mb="xl">
            {/* 1. Exchange Rate */}
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Paper p="md" radius="md" bg="dark.8" withBorder style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                    <Stack gap="xs">
                        <Group justify="space-between">
                            <Text size="xs" c="dimmed" fw={700}>USD/KRW</Text>
                            <ThemeIcon size="xs" color={exchange_rate.change_pct >= 0 ? "red" : "blue"} variant="light">
                                <IconCurrencyDollar size={12} />
                            </ThemeIcon>
                        </Group>
                        <Group align="flex-end" gap="xs">
                            <Text fw={700} size="xl">₩{exchange_rate.rate.toLocaleString()}</Text>
                            <Text size="sm" c={exchange_rate.change_pct >= 0 ? "red" : "blue"} fw={600} mb={2}>
                                {exchange_rate.change_pct > 0 ? "+" : ""}{exchange_rate.change_pct}%
                            </Text>
                        </Group>
                        <Text size="xs" c={exchange_rate.risk_level === 'normal' ? 'teal' : 'orange'}>
                            Risk: {exchange_rate.risk_level.toUpperCase()}
                        </Text>
                    </Stack>
                </Paper>
            </Grid.Col>

            {/* 2. Interest Spread */}
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Paper p="md" radius="md" bg="dark.8" withBorder style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                    <Stack gap="xs">
                        <Group justify="space-between">
                            <Text size="xs" c="dimmed" fw={700}>US-KR SPREAD</Text>
                            <ThemeIcon size="xs" color="blue" variant="light">
                                <IconChartBar size={12} />
                            </ThemeIcon>
                        </Group>
                        <Group align="flex-end" gap="xs">
                            <Text fw={700} size="xl">{interest_spread.spread_bp} bp</Text>
                            <Text size="xs" c="dimmed" mb={4}>
                                US {interest_spread.us_rate}% / KR {interest_spread.kr_rate}%
                            </Text>
                        </Group>
                        <Text size="xs" c={interest_spread.capital_risk === 'low' ? 'teal' : 'orange'}>
                            Capital Outflow: {interest_spread.capital_risk}
                        </Text>
                    </Stack>
                </Paper>
            </Grid.Col>

            {/* 3. FX Reserves */}
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Paper p="md" radius="md" bg="dark.8" withBorder style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                    <Stack gap="xs">
                        <Group justify="space-between">
                            <Text size="xs" c="dimmed" fw={700}>FX RESERVES</Text>
                            <ThemeIcon size="xs" color="green" variant="light">
                                <IconWorld size={12} />
                            </ThemeIcon>
                        </Group>
                        <Text fw={700} size="xl">${fx_reserves.current_reserves}B</Text>
                        <Text size="xs" c={fx_reserves.change >= 0 ? "teal" : "red"}>
                            MoM: {fx_reserves.change >= 0 ? "+" : ""}{fx_reserves.change}B
                        </Text>
                    </Stack>
                </Paper>
            </Grid.Col>

            {/* 4. Crisis Score */}
            <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
                <Paper p="xs" radius="md" bg="dark.8" withBorder style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                    <Group>
                        <RingProgress
                            size={70}
                            thickness={6}
                            roundCaps
                            sections={[{ value: crisis.crisis_score, color: getCrisisColor(crisis.crisis_level) }]}
                            label={
                                <Center>
                                    <Text fw={700} size="sm">{crisis.crisis_score}</Text>
                                </Center>
                            }
                        />
                        <Stack gap={0}>
                            <Text size="xs" c="dimmed" fw={700}>MARKET STRESS</Text>
                            <Text fw={700} size="sm" c={getCrisisColor(crisis.crisis_level)}>
                                {crisis.crisis_level.toUpperCase()}
                            </Text>
                            <Text size="xs" c="dimmed" style={{ fontSize: '10px' }}>{crisis.message}</Text>
                        </Stack>
                    </Group>
                </Paper>
            </Grid.Col>
        </Grid>
    );
}
