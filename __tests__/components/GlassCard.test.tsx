import React from 'react';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { GlassCard } from '@/components/ui/GlassCard';

// Wrapper for Mantine components
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MantineProvider>{children}</MantineProvider>
);

describe('GlassCard Component', () => {
    it('renders children correctly', () => {
        render(
            <TestWrapper>
                <GlassCard data-testid="glass-card">
                    <span>Test Content</span>
                </GlassCard>
            </TestWrapper>
        );

        expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders with glass-card testid', () => {
        render(
            <TestWrapper>
                <GlassCard data-testid="glass-card">Content</GlassCard>
            </TestWrapper>
        );

        const card = screen.getByTestId('glass-card');
        expect(card).toBeInTheDocument();
    });

    it('renders with custom delay prop', () => {
        render(
            <TestWrapper>
                <GlassCard delay={0.5}>Delayed Content</GlassCard>
            </TestWrapper>
        );

        expect(screen.getByText('Delayed Content')).toBeInTheDocument();
    });

    it('renders without hoverEffect when disabled', () => {
        render(
            <TestWrapper>
                <GlassCard hoverEffect={false} data-testid="no-hover-card">
                    No Hover Content
                </GlassCard>
            </TestWrapper>
        );

        expect(screen.getByText('No Hover Content')).toBeInTheDocument();
    });
});
