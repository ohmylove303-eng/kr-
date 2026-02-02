"use client";

import { Group, Button, Text } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { GlassCard } from "./ui/GlassCard";

export function Navigation() {
    const pathname = usePathname();

    const isActive = (path: string) => pathname === path;

    return (
        <header className="fixed top-6 left-0 right-0 z-50 flex justify-center pointer-events-none">
            <div className="pointer-events-auto">
                <GlassCard
                    p="xs"
                    radius="xl"
                    className="flex items-center gap-4 px-6 py-3"
                    style={{
                        backgroundColor: 'rgba(20, 20, 20, 0.6)',
                        backdropFilter: 'blur(30px)',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}
                >
                    <Group gap="lg">
                        <Link href="/" className="no-underline text-white">
                            <Text fw={700} size="sm">KR AI</Text>
                        </Link>

                        <Group gap="xs" visibleFrom="xs">
                            <Link href="/">
                                <Button
                                    variant={isActive("/") ? "light" : "subtle"}
                                    color="gray"
                                    size="xs"
                                    radius="xl"
                                >
                                    Dashboard
                                </Button>
                            </Link>
                            <Link href="/analysis">
                                <Button
                                    variant={isActive("/analysis") ? "light" : "subtle"}
                                    color="gray"
                                    size="xs"
                                    radius="xl"
                                >
                                    Analysis
                                </Button>
                            </Link>
                            <Link href="/themes">
                                <Button
                                    variant={isActive("/themes") ? "light" : "subtle"}
                                    color="gray"
                                    size="xs"
                                    radius="xl"
                                >
                                    Themes
                                </Button>
                            </Link>
                        </Group>
                        <IconSearch size={18} className="text-gray-400" />
                    </Group>
                </GlassCard>
            </div>
        </header>
    );
}
