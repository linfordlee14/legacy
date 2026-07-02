import type { Metadata } from "next";
import type { ReactNode } from "react";

import { EnvFooter } from "@/components/EnvFooter";

import "./globals.css";

export const metadata: Metadata = {
  title: "Legacy",
  description: "Your Life. Your Knowledge. Your Impact. Preserved Forever.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
        <EnvFooter />
      </body>
    </html>
  );
}
