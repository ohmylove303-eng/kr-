import type { Metadata } from "next";
import { ColorSchemeScript } from "@mantine/core";
import { Providers } from "@/components/Providers";
import "./globals.css";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";

export const metadata: Metadata = {
  title: "KR Market AI | Premium Dashboard",
  description: "Advanced AI Stock Analysis System",
};

import { Navigation } from "@/components/Navigation";

// ...

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ColorSchemeScript />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
      </head>
      <body>
        <Providers>
          <Navigation />
          {children}
        </Providers>
      </body>
    </html>
  );
}
