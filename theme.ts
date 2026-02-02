import { createTheme, rem } from '@mantine/core';

export const theme = createTheme({
    colors: {
        // Apple 'Midnight' & 'Dark Titanium' Inspired Palette
        dark: [
            '#C1C2C5', // 0: Text Light (Secondary)
            '#A6A7AB', // 1: Text Dimmed
            '#909296', // 2: Icon Inactive
            '#5C5F66', // 3: Border Dimmed
            '#373A40', // 4: Card BG (Light)
            '#2C2E33', // 5: Card BG (Default)
            '#25262B', // 6: App BG (Light)
            '#1A1B1E', // 7: App BG (Dark - Main) - Apple iPhone Black
            '#141517', // 8: Sidebar BG
            '#101113', // 9: Pure Black
        ],
        // 'Pacific Blue' Accent
        primary: [
            '#E7F5FF', '#D0EBFF', '#A5D8FF', '#74C0FC', '#4DABF7',
            '#339AF0', '#228BE6', '#1C7ED6', '#1971C2', '#1864AB',
        ],
    },
    primaryColor: 'primary',
    defaultRadius: 'lg', // 1rem default
    radius: {
        xs: rem(4),
        sm: rem(8),
        md: rem(12),
        lg: rem(20), // Standard Card Radius
        xl: rem(32), // "Bento" Radius
    },
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',
    headings: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        sizes: {
            h1: { fontSize: rem(48), lineHeight: '1.2' },
            h2: { fontSize: rem(34), lineHeight: '1.3' },
            h3: { fontSize: rem(24), lineHeight: '1.35' },
        },
    },
    components: {
        Paper: {
            defaultProps: {
                radius: 'xl',
            },
            styles: (theme: any) => ({
                root: {
                    backgroundColor: 'rgba(30, 30, 30, 0.4)', // Glass base
                    backdropFilter: 'blur(20px)',
                    WebkitBackdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
                },
            }),
        },
        AppShell: {
            styles: (theme: any) => ({
                main: {
                    backgroundColor: '#000000', // Pure Black for OLED feel
                    color: '#FFFFFF',
                }
            })
        }
    },
});
