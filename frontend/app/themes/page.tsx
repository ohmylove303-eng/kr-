"use client";

import { Container, Stack, Text, SimpleGrid } from "@mantine/core";
import { PageTitle } from "@/components/ui/PageTitle";
import { SectorGrid } from "@/components/SectorGrid";

export default function ThemesPage() {
    return (
        <main className="min-h-screen bg-black pb-20">
            <Container size="xl" pt={120}>
                <PageTitle
                    title="Themes & Sectors"
                    subtitle="Market Flow and Sector Performance"
                />

                {/* 1. Sector Grid */}
                <Stack mb={40}>
                    <Text fw={700} c="dimmed" size="sm">SECTOR PERFORMANCE</Text>
                    <SectorGrid />
                </Stack>

                {/* 2. Theme List (Future) */}
                <Stack>
                    <Text fw={700} c="dimmed" size="sm">HOT THEMES</Text>
                    <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
                        {/* Placeholder for Themes */}
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10 opacity-50">
                            <Text fw={700}>Defense (방산)</Text>
                            <Text size="sm" c="dimmed">Detailed analysis coming soon...</Text>
                        </div>
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10 opacity-50">
                            <Text fw={700}>Semiconductor (반도체)</Text>
                            <Text size="sm" c="dimmed">Detailed analysis coming soon...</Text>
                        </div>
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10 opacity-50">
                            <Text fw={700}>AI / Power (AI전력)</Text>
                            <Text size="sm" c="dimmed">Detailed analysis coming soon...</Text>
                        </div>
                    </SimpleGrid>
                </Stack>
            </Container>
        </main>
    );
}
