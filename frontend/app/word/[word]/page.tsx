"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { wordApi, WordDetail } from "@/lib/api";
import PurchaseModalWithPayment from "@/components/PurchaseModalWithPayment";

export default function WordPage() {
  const params = useParams();
  const wordText = params.word as string;

  const [word, setWord] = useState<WordDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>("");
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);

  useEffect(() => {
    loadWord();
  }, [wordText]);

  // Countdown timer
  useEffect(() => {
    if (!word || !word.lockout_ends_at || word.is_available) {
      setTimeRemaining("");
      return;
    }

    const updateTimer = () => {
      const now = new Date().getTime();
      const end = new Date(word.lockout_ends_at!).getTime();
      const distance = end - now;

      if (distance < 0) {
        setTimeRemaining("EXPIRED");
        // Reload word data when lockout expires
        loadWord();
        return;
      }

      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      let timeStr = "";
      if (days > 0) timeStr += `${days}d `;
      timeStr += `${hours.toString().padStart(2, "0")}:${minutes
        .toString()
        .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

      setTimeRemaining(timeStr);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [word]);

  const loadWord = async () => {
    try {
      setLoading(true);
      const data = await wordApi.getWord(wordText);
      setWord(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Word not found");
    } finally {
      setLoading(false);
    }
  };

  const handlePurchaseSuccess = () => {
    setShowPurchaseModal(false);
    loadWord();
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-lg text-gray-600">Loading...</p>
      </div>
    );
  }

  if (error || !word) {
    const handleGetRandom = async () => {
      try {
        const randomWord = await wordApi.getRandom();
        window.location.href = `/word/${randomWord.text}`;
      } catch (err) {
        console.error("Failed to get random word:", err);
      }
    };

    const handleAddSuccess = () => {
      setShowPurchaseModal(false);
      loadWord();
    };

    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-lg text-red-600 mb-6">{error || "Word not found"}</p>
        <p className="text-gray-600 mb-8">
          This word isn&apos;t in our registry yet. You can add it for $50 and own it for 50 hours!
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setShowPurchaseModal(true)}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add &quot;{wordText}&quot; for $50
          </button>
          <button
            onClick={handleGetRandom}
            className="px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
          >
            Try a Random Word
          </button>
        </div>

        {/* Add Word Modal */}
        {showPurchaseModal && (
          <PurchaseModalWithPayment
            word={wordText}
            price="50"
            isAddingWord={true}
            onClose={() => setShowPurchaseModal(false)}
            onSuccess={handleAddSuccess}
          />
        )}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Word Header */}
      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <h1 className="text-5xl font-bold text-gray-900 mb-4 text-center">
          {word.text}
        </h1>

        {/* Status Badge */}
        <div className="text-center mb-6">
          {word.is_available ? (
            <span className="inline-block px-6 py-2 bg-green-100 text-green-800 font-semibold rounded-full">
              ✓ Available
            </span>
          ) : (
            <span className="inline-block px-6 py-2 bg-yellow-100 text-yellow-800 font-semibold rounded-full">
              🔒 Locked
            </span>
          )}
        </div>

        {/* Price */}
        <div className="text-center mb-6">
          <p className="text-4xl font-bold text-blue-600">${word.price}</p>
          <p className="text-sm text-gray-500 mt-1">
            {word.is_available ? "Purchase Price" : "Next Purchase Price"}
          </p>
        </div>

        {/* Countdown Timer */}
        {!word.is_available && timeRemaining && (
          <div className="text-center mb-6 p-4 bg-yellow-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Time Remaining</p>
            <p className="text-3xl font-mono font-bold text-yellow-800">
              {timeRemaining}
            </p>
          </div>
        )}

        {/* Owner Info */}
        {word.owner_name && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-700 mb-2">Current Owner</h3>
            <p className="text-lg font-bold text-gray-900">{word.owner_name}</p>
            {word.owner_message && (
              <div className="mt-3">
                <h4 className="font-semibold text-gray-700 mb-1">Message</h4>
                <p className="text-gray-800 italic">&quot;{word.owner_message}&quot;</p>
              </div>
            )}
          </div>
        )}

        {/* Purchase Button */}
        {word.is_available ? (
          <button
            onClick={() => setShowPurchaseModal(true)}
            className="w-full py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Claim for ${word.price}
          </button>
        ) : (
          <div className="text-center text-gray-500">
            This word is currently locked. Come back when the timer expires!
          </div>
        )}
      </div>

      {/* Transaction History */}
      {word.transactions.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Transaction History ({word.transaction_count})
          </h2>
          <div className="space-y-3">
            {word.transactions.map((transaction) => (
              <div
                key={transaction.id}
                className="p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold text-gray-900">
                      {transaction.buyer_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(transaction.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <p className="text-green-600 font-bold">
                    ${transaction.price_paid}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Purchase Modal */}
      {showPurchaseModal && (
        <PurchaseModalWithPayment
          word={word.text}
          price={String(word.price)}
          onClose={() => setShowPurchaseModal(false)}
          onSuccess={handlePurchaseSuccess}
        />
      )}
    </div>
  );
}
