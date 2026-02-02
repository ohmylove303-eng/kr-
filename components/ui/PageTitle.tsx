"use client";

import { Title } from "@mantine/core";
import { motion } from "framer-motion";

export function PageTitle({ title, subtitle }: { title: string; subtitle?: string }) {
    return (
        <div className="mb-8 pl-1">
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
            >
                <Title
                    order={1}
                    style={{
                        fontSize: "3.5rem",
                        fontWeight: 800,
                        letterSpacing: "-0.03em",
                        background: "linear-gradient(135deg, #FFFFFF 0%, #A6A7AB 100%)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                        marginBottom: "0.2rem",
                    }}
                >
                    {title}
                </Title>
                {subtitle && (
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="text-gray-400 text-xl font-medium tracking-tight"
                    >
                        {subtitle}
                    </motion.p>
                )}
            </motion.div>
        </div>
    );
}
