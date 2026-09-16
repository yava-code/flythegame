import type { Metadata, Viewport } from "next";
import { Syne, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const plex = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

const site = "https://flythegame.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(site),
  title: "Fly Swatter · MaleCNS",
  description:
    "A fruit-fly connectome in a fly swatter. The fly never sees your hand — only the shadow. MaleCNS v1.0, ~166k neurons, frozen weights.",
  openGraph: {
    title: "Fly Swatter · MaleCNS",
    description:
      "the fly sees the SHADOW, not the hand. slap the freeze. DNp01 burst = gone.",
    url: site,
    siteName: "Fly Swatter",
    images: [{ url: "/og.png", width: 1536, height: 1024, alt: "Fly Swatter" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Fly Swatter · MaleCNS",
    description:
      "I put the MaleCNS fruit-fly brain (~166k neurons) in a fly swatter.",
    images: ["/og.png"],
  },
};

export const viewport: Viewport = {
  themeColor: "#071018",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${syne.variable} ${plex.variable}`}>
      <body>{children}</body>
    </html>
  );
}
