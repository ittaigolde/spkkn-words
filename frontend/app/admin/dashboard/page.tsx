"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  getDashboard,
  resetWord,
  adminLogout,
  adminTokenStorage,
  DashboardData,
} from "@/lib/adminApi";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetForm, setResetForm] = useState({
    word: "",
    new_price: "",
    owner_name: "",
    owner_message: "",
  });
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is authenticated
    if (!adminTokenStorage.get()) {
      router.push("/admin/login");
      return;
    }

    loadDashboard();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboard, 30000);
    return () => clearInterval(interval);
  }, [router]);

  const loadDashboard = async () => {
    try {
      const data = await getDashboard();
      setDashboard(data);
      setError(null);
    } catch (err: any) {
      if (err.message.includes("401") || err.message.includes("token")) {
        // Token expired or invalid, redirect to login
        adminLogout();
        router.push("/admin/login");
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    adminLogout();
    router.push("/admin/login");
  };

  const handleResetWord = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetError(null);
    setResetLoading(true);

    try {
      await resetWord({
        word: resetForm.word.trim().toLowerCase(),
        new_price: parseFloat(resetForm.new_price),
        owner_name: resetForm.owner_name.trim() || undefined,
        owner_message: resetForm.owner_message.trim() || undefined,
      });

      // Success - close modal and reload dashboard
      setShowResetModal(false);
      setResetForm({ word: "", new_price: "", owner_name: "", owner_message: "" });
      await loadDashboard();
    } catch (err: any) {
      setResetError(err.message);
    } finally {
      setResetLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-red-600 mb-2">Error</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => router.push("/admin/login")}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <div className="flex gap-3">
              <button
                onClick={() => router.push("/admin/abuse")}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                Content Moderation
              </button>
              <button
                onClick={() => setShowResetModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Reset Word
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Income Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Total Income</h3>
            <p className="text-3xl font-bold text-gray-900">
              ${dashboard.income.total_income.toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {dashboard.income.total_transactions} transactions
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Today&apos;s Income</h3>
            <p className="text-3xl font-bold text-green-600">
              ${dashboard.income.today_income.toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {dashboard.income.today_transactions} transactions
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">This Week&apos;s Income</h3>
            <p className="text-3xl font-bold text-blue-600">
              ${dashboard.income.week_income.toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {dashboard.income.week_transactions} transactions
            </p>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Total Words</h3>
            <p className="text-2xl font-bold text-gray-900">{dashboard.stats.total_words}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Available Words</h3>
            <p className="text-2xl font-bold text-green-600">{dashboard.stats.available_words}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Locked Words</h3>
            <p className="text-2xl font-bold text-yellow-600">{dashboard.stats.locked_words}</p>
          </div>
        </div>

        {/* Popular Words */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Most Viewed Words (Last 30 Days)
            </h2>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Word
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Price
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Owner
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Views
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {dashboard.popular_words.map((word) => (
                    <tr key={word.word} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {word.word}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">${word.price}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {word.owner || "—"}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-right font-semibold">
                        {word.views}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Recent Errors */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Errors</h2>
          </div>
          <div className="p-6">
            {dashboard.recent_errors.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No recent errors</p>
            ) : (
              <div className="space-y-4">
                {dashboard.recent_errors.slice(0, 10).map((error) => (
                  <div key={error.id} className="border border-red-200 rounded-lg p-4 bg-red-50">
                    <div className="flex justify-between items-start mb-2">
                      <span className="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                        {error.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(error.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900 font-medium mb-1">{error.message}</p>
                    {error.endpoint && (
                      <p className="text-xs text-gray-600">Endpoint: {error.endpoint}</p>
                    )}
                    {error.user_info && (
                      <p className="text-xs text-gray-600">User: {error.user_info}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reset Word Modal */}
      {showResetModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Reset Word</h2>

            <form onSubmit={handleResetWord}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Word
                  </label>
                  <input
                    type="text"
                    value={resetForm.word}
                    onChange={(e) => setResetForm({ ...resetForm, word: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="hello"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Price ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    value={resetForm.new_price}
                    onChange={(e) => setResetForm({ ...resetForm, new_price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="1.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Owner Name (optional)
                  </label>
                  <input
                    type="text"
                    value={resetForm.owner_name}
                    onChange={(e) => setResetForm({ ...resetForm, owner_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Leave empty to clear owner"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Owner Message (optional)
                  </label>
                  <textarea
                    value={resetForm.owner_message}
                    onChange={(e) => setResetForm({ ...resetForm, owner_message: e.target.value })}
                    maxLength={140}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional message"
                  />
                </div>

                {resetError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">{resetError}</p>
                  </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-800">
                    ⚠️ This will create an admin transaction that won&apos;t count towards revenue stats.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowResetModal(false);
                    setResetError(null);
                    setResetForm({ word: "", new_price: "", owner_name: "", owner_message: "" });
                  }}
                  className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {resetLoading ? "Resetting..." : "Reset Word"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
