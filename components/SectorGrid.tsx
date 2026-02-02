"use client";

import { Grid, Paper, Text, Stack } from "@mantine/core";
import useSWR from "swr";
import { fetchSectorPerformance } from "@/lib/api";

export function SectorGrid() {
    const { data, isLoading } = useSWR("sector-performance", fetchSectorPerformance, { refreshInterval: 120000 });

    if (isLoading || !data || !data.sectors) return null;

    return (
        <Grid gutter="xs" mt="md">
            {data.sectors.map((sector) => {
                const isPositive = sector.change_pct >= 0;
                const color = isPositive ? "red" : "blue"; // KR Market Style
                const bgColor = isPositive ? "rgba(255, 100, 100, 0.1)" : "rgba(100, 100, 255, 0.1)";

                return (
                    <Grid.Col key={sector.name} span={{ base: 6, sm: 4, md: 2 }}>
                        <Paper
                            p="xs"
                            radius="md"
                            bg="dark.8"
                            withBorder
                            style={{
                                borderColor: 'rgba(255,255,255,0.05)',
                                backgroundColor: bgColor
                            }}
                        >
                            <Stack gap={0} align="center">
                                <Text size="xs" fw={700} c="gray.3" truncate w="100%" ta="center">
                                    {sector.name}
                                </Text>
                                <Text size="sm" fw={800} c={color}>
                                    {isPositive ? "+" : ""}{sector.change_pct.toFixed(2)}%
                                </Text>
                                <Text size="xs" c="dimmed" style={{ fontSize: '9px' }}>
                                    {(sector.volume / 1000000).toFixed(1)}M Vol
                                </Text>
                            </Stack>
                        </Paper>
                    </Grid.Col>
                );
            })}
        </Grid>
    );
}
