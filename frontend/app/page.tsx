"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { wordApi, leaderboardApi, Word, Transaction } from "@/lib/api";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [randomWord, setRandomWord] = useState<Word | null>(null);
  const [mostExpensive, setMostExpensive] = useState<Word[]>([]);
  const [recentPurchases, setRecentPurchases] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);

  // Load leaderboards on mount
  useEffect(() => {
    loadLeaderboards();
  }, []);

  const loadLeaderboards = async () => {
    try {
      const [expensive, recent] = await Promise.all([
        leaderboardApi.getMostExpensive(10),
        leaderboardApi.getRecent(10),
      ]);
      setMostExpensive(expensive);
      setRecentPurchases(recent);
    } catch (error) {
      console.error("Failed to load leaderboards:", error);
    }
  };

  const handleGetRandom = async () => {
    setLoading(true);
    try {
      const word = await wordApi.getRandom();
      setRandomWord(word);
    } catch (error) {
      console.error("Failed to get random word:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/word/${searchQuery.toLowerCase().trim()}`;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          Own a Word. For Now.
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Every word starts at $1. Each purchase increases the price by $1 and locks
          it for 1 hour per dollar spent. When time runs out, anyone can steal it.
        </p>
      </div>

      {/* Search Section */}
      <div className="max-w-2xl mx-auto mb-12">
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for a word..."
            className="flex-1 px-6 py-4 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Random Word Button */}
      <div className="text-center mb-12">
        <button
          onClick={handleGetRandom}
          disabled={loading}
          className="px-8 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
        >
          {loading ? "Loading..." : "Show Me a Random $1 Word"}
        </button>
        {randomWord && (
          <div className="mt-4 p-6 bg-white rounded-lg shadow-md inline-block">
            <p className="text-2xl font-bold text-gray-900 mb-2">
              {randomWord.text}
            </p>
            <p className="text-green-600 font-semibold mb-3">
              ${randomWord.price} • Available
            </p>
            <Link
              href={`/word/${randomWord.text}`}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-block"
            >
              Claim This Word
            </Link>
          </div>
        )}
      </div>

      {/* Leaderboards */}
      <div className="grid md:grid-cols-2 gap-8 mt-12">
        {/* Most Expensive */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            💰 Most Expensive Words
          </h3>
          <div className="space-y-3">
            {mostExpensive.map((word, index) => (
              <Link
                key={word.id}
                href={`/word/${word.text}`}
                className="block p-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <span className="text-lg font-bold text-gray-400 flex-shrink-0">
                      #{index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-gray-900 block">
                        {word.text}
                      </span>
                      {!word.is_available && word.owner_name && (
                        <p className="text-sm text-gray-500 mt-1">
                          🔒 {word.owner_name}
                        </p>
                      )}
                      {word.owner_message && (
                        <p className="text-sm text-gray-600 italic mt-1 truncate">
                          &quot;{word.owner_message}&quot;
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-blue-600 font-bold flex-shrink-0 ml-3">
                    ${word.price}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Purchases */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            🔥 Recent Purchases
          </h3>
          <div className="space-y-3">
            {recentPurchases.map((transaction) => (
              <div
                key={transaction.id}
                className="p-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-gray-900">
                    {transaction.buyer_name}
                  </span>
                  <span className="text-green-600 font-bold">
                    ${transaction.price_paid}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {new Date(transaction.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
