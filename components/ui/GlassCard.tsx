"use client";

import { Paper, PaperProps } from "@mantine/core";
import { motion } from "framer-motion";

interface GlassCardProps extends PaperProps {
    children: React.ReactNode;
    delay?: number;
    hoverEffect?: boolean;
}

// @ts-ignore: Mantine generic component typing conflict with Framer Motion
const MotionPaper = motion(Paper as any);

export function GlassCard({
    children,
    delay = 0,
    hoverEffect = true,
    style,
    ...props
}: GlassCardProps) {
    return (
        // @ts-ignore: Mantine & Framer Motion typing conflict workaround
        <MotionPaper
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay, ease: "easeOut" }}
            whileHover={
                hoverEffect
                    ? {
                        scale: 1.02,
                        backgroundColor: "rgba(40, 40, 40, 0.6)",
                        transition: { duration: 0.2 },
                    }
                    : {}
            }
            style={{
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                // Apple-style subtle gradient border
                border: "1px solid rgba(255, 255, 255, 0.12)",
                // Deep shadow for depth
                boxShadow: "0 10px 40px -10px rgba(0,0,0,0.5)",
                overflow: "hidden",
                ...style,
            }}
            {...props}
        >
            {children}
        </MotionPaper>
    );
}
