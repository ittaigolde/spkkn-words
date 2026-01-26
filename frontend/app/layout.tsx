import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import CookieBanner from "@/components/CookieBanner";

export const metadata: Metadata = {
  title: "The Word Registry",
  description: "A competitive marketplace for exclusive, temporary ownership of English words",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-gray-50">
        <Header />
        <main>{children}</main>
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-xs text-gray-500 text-center">
              Ownership is a digital novelty service for entertainment purposes only.
              Purchase does not convey legal trademark rights, copyright, or exclusivity
              over the English language outside of this platform.
            </p>
          </div>
        </footer>
        <CookieBanner />
      </body>
    </html>
  );
}
