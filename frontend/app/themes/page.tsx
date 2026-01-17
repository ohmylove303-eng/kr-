"use client";

import { Container, Stack, Text, SimpleGrid, Badge, Skeleton } from "@mantine/core";
import { PageTitle } from "@/components/ui/PageTitle";
import { SectorGrid } from "@/components/SectorGrid";
import useSWR from "swr";
import { fetchHotThemes } from "@/lib/api";

subtitle = "Market Flow and Sector Performance"
    />

    {/* 1. Sector Grid */ }
    < Stack mb = { 40} >
                <Text fw={700} c="dimmed" size="sm">SECTOR PERFORMANCE</Text>
                <SectorGrid />
            </Stack >

    {/* 2. Theme List (Now Dynamic with AI) */ }
    < Stack >
                <Text fw={700} c="dimmed" size="sm">HOT THEMES (AI ANALYSIS)</Text>
                <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
                    {isLoading ? (
                        // Loading Skeletons
                        Array(3).fill(0).map((_, i) => (
                            <div key={i} className="p-6 rounded-xl bg-white/5 border border-white/10 opacity-50">
                                <Skeleton height={24} width="50%" mb="md" visible={true} />
                                <Skeleton height={80} visible={true} />
                            </div>
                        ))
                    ) : themeData?.themes ? (
                        themeData.themes.map((theme) => {
                            const outlookColor = theme.outlook === 'Positive' ? 'green' : theme.outlook === 'Negative' ? 'red' : 'gray';
                            return (
                                <div key={theme.name} className="p-6 rounded-xl bg-white/5 border border-white/10">
                                    <div className="flex justify-between items-start mb-2">
                                        <Text fw={700} size="lg">{theme.name}</Text>
                                        <Badge color={outlookColor} variant="light">{theme.outlook}</Badge>
                                    </div>
                                    <Text size="sm" c="gray.3" style={{ lineHeight: 1.6 }}>
                                        {theme.analysis}
                                    </Text>
                                </div>
                            );
                        })
                    ) : (
                        // Error or Empty State
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                            <Text c="dimmed">No theme analysis available.</Text>
                        </div>
                    )}
                </SimpleGrid>
            </Stack >
        </Container >
    </main >
);
}
