"use client";

export default function DemoBanner() {
  // Only show in production with demo mode enabled
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

  if (!isDemoMode) return null;

  return (
    <div className="bg-yellow-500 text-gray-900 py-2 px-4 text-center text-sm font-medium">
      🧪 Demo Mode - This is a demonstration using Stripe test payments. Use test card: 4242 4242 4242 4242
    </div>
  );
}
