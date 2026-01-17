"use client";

import { Table, Badge, Text, Group, Stack, Progress, Tooltip, ThemeIcon } from "@mantine/core";
import { IconRobot, IconTrendingUp, IconTrendingDown, IconMinus } from "@tabler/icons-react";
import { Signal } from "@/lib/api";

interface SignalTableProps {
    signals: Signal[];
    onRowClick?: (signal: Signal) => void;
}

export function SignalTable({ signals, onRowClick }: SignalTableProps) {
    const rows = signals.map((sig, index) => {
        // 1. AI Consensus Logic
        const gptAction = sig.gpt_recommendation?.action || "HOLD";
        const geminiAction = sig.gemini_recommendation?.action || "HOLD";

        const getActionColor = (action: string) => {
            if (action === "BUY") return "teal";
            if (action === "SELL") return "red";
            return "gray";
        };

        // 2. Supply Formatting (KR Syle: Buy=Red/Positive, Sell=Blue/Negative)
        const formatSupply = (val?: number) => {
            if (!val) return <Text size="xs" c="dimmed">-</Text>;
            const absVal = Math.abs(val);
            const isBuy = val > 0;
            const color = isBuy ? "red" : "blue"; // KR Market Standard
            const sign = isBuy ? "+" : "";

            let formatted = "";
            if (absVal >= 1000000) formatted = `${(absVal / 1000000).toFixed(1)}M`;
            else if (absVal >= 1000) formatted = `${(absVal / 1000).toFixed(1)}K`;
            else formatted = absVal.toString();

            return <Text size="xs" c={color} fw={700}>{sign}{formatted}</Text>;
        };

        // 3. NICE Score Color (Aligned with Modal: Total Score / 300 * 100)
        let niceScore = 0;
        if (sig.nice_layers?.total) {
            niceScore = (sig.nice_layers.total / 300) * 100;
        } else if (sig.score) {
            // Fallback: if score is large (>100), assume it's raw total out of 300
            niceScore = sig.score > 100 ? (sig.score / 300) * 100 : sig.score;
        }

        const progressColor = niceScore >= 80 ? "teal" : niceScore >= 50 ? "yellow" : "gray";

        return (
            <Table.Tr
                key={sig.ticker}
                className="hover:bg-white/5 transition-colors cursor-pointer"
                onClick={() => onRowClick && onRowClick(sig)}
            >
                {/* AI Consensus */}
                <Table.Td>
                    <Stack gap={4} align="center">
                        <Group gap={4}>
                            <ThemeIcon size="xs" color={getActionColor(gptAction)} variant="light">
                                <IconRobot size={10} />
                            </ThemeIcon>
                            <Text size="xs" fw={700} c={getActionColor(gptAction)} style={{ fontSize: '10px' }}>GPT</Text>
                        </Group>
                        <Group gap={4}>
                            <ThemeIcon size="xs" color={getActionColor(geminiAction)} variant="light">
                                <IconRobot size={10} />
                            </ThemeIcon>
                            <Text size="xs" fw={700} c={getActionColor(geminiAction)} style={{ fontSize: '10px' }}>GEM</Text>
                        </Group>
                    </Stack>
                </Table.Td>

                {/* Stock Info */}
                <Table.Td>
                    <Stack gap={2}>
                        <Group gap={6}>
                            <Text fw={700} size="sm">{sig.name}</Text>
                            {sig.theme && <Badge size="xs" variant="outline" color="gray" style={{ fontSize: '9px', height: '16px' }}>{sig.theme}</Badge>}
                        </Group>
                        <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>{sig.ticker}</Text>
                    </Stack>
                </Table.Td>

                {/* NICE Total Score */}
                <Table.Td>
                    <Stack gap={2} w={80}>
                        <Group justify="space-between">
                            <Text size="xs" c="dimmed" style={{ fontSize: '9px' }}>Total Score</Text>
                            <Text size="xs" fw={700} c={progressColor}>{Math.round(niceScore)}</Text>
                        </Group>
                        <Progress value={niceScore} size="sm" color={progressColor} />
                    </Stack>
                </Table.Td>

                {/* Supply Flow */}
                <Table.Td>
                    <Stack gap={2} align="flex-end">
                        <Group gap={4}>
                            <Text size="xs" c="dimmed" style={{ fontSize: '9px' }}>For.</Text>
                            {formatSupply(sig.foreign_5d)}
                        </Group>
                        <Group gap={4}>
                            <Text size="xs" c="dimmed" style={{ fontSize: '9px' }}>Inst.</Text>
                            {formatSupply(sig.inst_5d)}
                        </Group>
                    </Stack>
                </Table.Td>

                {/* Prices */}
                <Table.Td style={{ textAlign: 'right' }}>
                    <Stack gap={2}>
                        <Text fw={700} size="sm">₩{sig.current_price.toLocaleString()}</Text>
                        <Group gap={4} justify="flex-end">
                            <Text size="xs" c="dimmed" style={{ fontSize: '9px' }}>TP1</Text>
                            <Text size="xs" c="teal">₩{(sig.tp1 || 0).toLocaleString()}</Text>
                        </Group>
                    </Stack>
                </Table.Td>

                {/* Return */}
                <Table.Td style={{ textAlign: 'right' }}>
                    <Badge
                        size="lg"
                        variant="light"
                        color={sig.return_pct >= 0 ? "red" : "blue"} // KR Market Color
                        radius="sm"
                    >
                        {sig.return_pct > 0 ? "+" : ""}{sig.return_pct.toFixed(2)}%
                    </Badge>
                </Table.Td>
            </Table.Tr>
        );
    });

    return (
        <Table verticalSpacing="xs" highlightOnHover>
            <Table.Thead>
                <Table.Tr>
                    <Table.Th w={60} style={{ textAlign: 'center' }}>AI</Table.Th>
                    <Table.Th>Stock</Table.Th>
                    <Table.Th w={100}>NICE Score</Table.Th>
                    <Table.Th style={{ textAlign: 'right' }}>Supply (5D)</Table.Th>
                    <Table.Th style={{ textAlign: 'right' }}>Price / TP</Table.Th>
                    <Table.Th style={{ textAlign: 'right' }}>Return</Table.Th>
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
        </Table>
    );
}
