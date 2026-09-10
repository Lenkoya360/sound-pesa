import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { config } from "@/lib/config";
import { PWAInit } from "@/components/pwa-init";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: config.NEXT_PUBLIC_APP_NAME,
    template: `%s | ${config.NEXT_PUBLIC_APP_NAME}`,
  },
  description: config.NEXT_PUBLIC_APP_DESCRIPTION,
  keywords: [
    "cryptocurrency",
    "blockchain",
    "bitcoin",
    "ethereum",
    "cardano",
    "polkadot",
    "wallet",
    "defi",
    "crypto",
    "sound pesa",
  ],
  authors: [{ name: "Sound Pesa Team" }],
  creator: "Sound Pesa Team",
  publisher: "Sound Pesa",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(
    config.NODE_ENV === "production" 
      ? "https://soundpesa.com" 
      : "http://localhost:3000"
  ),
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: config.NEXT_PUBLIC_APP_NAME,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    title: config.NEXT_PUBLIC_APP_NAME,
    description: config.NEXT_PUBLIC_APP_DESCRIPTION,
    siteName: config.NEXT_PUBLIC_APP_NAME,
    images: [
      {
        url: "/icons/icon-512x512.png",
        width: 512,
        height: 512,
        alt: config.NEXT_PUBLIC_APP_NAME,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: config.NEXT_PUBLIC_APP_NAME,
    description: config.NEXT_PUBLIC_APP_DESCRIPTION,
    creator: "@soundpesa",
    images: ["/icons/icon-512x512.png"],
  },
  robots: {
    index: config.NODE_ENV === "production",
    follow: config.NODE_ENV === "production",
    googleBot: {
      index: config.NODE_ENV === "production",
      follow: config.NODE_ENV === "production",
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    // Add verification tokens when available
    // google: "verification-token",
    // yandex: "verification-token",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes" />
        <meta name="theme-color" content="#2563eb" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content={config.NEXT_PUBLIC_APP_NAME} />
        <meta name="application-name" content={config.NEXT_PUBLIC_APP_NAME} />
        <meta name="msapplication-TileColor" content="#2563eb" />
        <meta name="msapplication-config" content="/browserconfig.xml" />
        
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
        
        {/* Preload critical resources */}
        <link rel="preload" href="/icons/icon-192x192.png" as="image" />
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="preconnect" href="//fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased min-h-screen bg-white font-sans`}
        suppressHydrationWarning
      >
        <PWAInit>
          <div id="root" className="relative flex min-h-screen flex-col">
            {children}
          </div>
        </PWAInit>
      </body>
    </html>
  );
}
