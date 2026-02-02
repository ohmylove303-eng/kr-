"use client";

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { Text, Stack } from "@mantine/core";

interface NiceLayerData {
    subject: string;
    A: number; // Current Score
    fullMark: number;
}

interface NiceRadarChartProps {
    data?: NiceLayerData[];
    score: number;
}

export function NiceRadarChart({ data, score }: NiceRadarChartProps) {
    // Default data structure if not provided
    const chartData = data || [
        { subject: 'Technical', A: 0, fullMark: 100 },
        { subject: 'Supply', A: 0, fullMark: 100 },
        { subject: 'Sentiment', A: 0, fullMark: 100 },
        { subject: 'Macro', A: 0, fullMark: 100 },
        { subject: 'Inst.', A: 0, fullMark: 100 },
    ];

    return (
        <Stack align="center" gap={0} pos="relative">
            <div style={{ width: 200, height: 200, minWidth: 200, minHeight: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                        <PolarGrid gridType="polygon" stroke="rgba(255,255,255,0.3)" />
                        <PolarAngleAxis
                            dataKey="subject"
                            tick={{ fill: '#888', fontSize: 10 }}
                        />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                        <Radar
                            name="NICE Score"
                            dataKey="A"
                            stroke="#00E396"
                            strokeWidth={2}
                            fill="#00E396"
                            fillOpacity={0.3}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>

            {/* Center Score Overlay */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 mt-[10px]">
                <Text size="xl" fw={900} c={score >= 80 ? "teal" : score >= 50 ? "yellow" : "gray"}>
                    {score}
                </Text>
            </div>
        </Stack>
    );
}
