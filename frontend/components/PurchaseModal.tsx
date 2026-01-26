"use client";

import { useState } from "react";
import { wordApi } from "@/lib/api";

interface PurchaseModalProps {
  word: string;
  price: string;
  isAddingWord?: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PurchaseModal({
  word,
  price,
  isAddingWord = false,
  onClose,
  onSuccess,
}: PurchaseModalProps) {
  const [ownerName, setOwnerName] = useState("");
  const [ownerMessage, setOwnerMessage] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate lockout hours
  const priceNum = parseFloat(price);
  const lockoutHours = priceNum;
  const lockoutDays = Math.floor(lockoutHours / 24);
  const remainingHours = lockoutHours % 24;

  let lockoutText = "";
  if (lockoutDays > 0) {
    lockoutText = `${lockoutDays} day${lockoutDays > 1 ? "s" : ""} and ${remainingHours} hour${remainingHours !== 1 ? "s" : ""}`;
  } else {
    lockoutText = `${lockoutHours} hour${lockoutHours !== 1 ? "s" : ""}`;
  }

  const validateContent = (text: string): string | null => {
    // Check for URLs
    if (/https?:\/\/|www\.|\.com|\.net|\.org|\.io|\.ai/i.test(text)) {
      return "URLs and web links are not allowed";
    }

    // Check for email addresses
    if (/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/.test(text)) {
      return "Email addresses are not allowed";
    }

    // Check for social media handles
    if (/@\w+/.test(text)) {
      return "Social media handles are not allowed";
    }

    // Check for phone numbers
    if (/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/.test(text)) {
      return "Phone numbers are not allowed";
    }

    // Basic profanity check
    const profanity = ["fuck", "shit", "bitch", "asshole", "damn"];
    const lowerText = text.toLowerCase();
    for (const word of profanity) {
      if (lowerText.includes(word)) {
        return "Profanity is not allowed";
      }
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate inputs
    if (ownerName.trim().length === 0) {
      setError("Please enter your name");
      return;
    }

    if (ownerMessage.trim().length === 0) {
      setError("Please enter a message");
      return;
    }

    if (ownerMessage.length > 140) {
      setError("Message must be 140 characters or less");
      return;
    }

    // Validate content
    const nameError = validateContent(ownerName);
    if (nameError) {
      setError(nameError);
      return;
    }

    const messageError = validateContent(ownerMessage);
    if (messageError) {
      setError(messageError);
      return;
    }

    if (!acknowledged) {
      setError("You must acknowledge the terms to proceed");
      return;
    }

    // Submit purchase or add word
    setLoading(true);
    try {
      if (isAddingWord) {
        await wordApi.addWord(word, ownerName.trim(), ownerMessage.trim());
      } else {
        await wordApi.purchase(word, ownerName.trim(), ownerMessage.trim());
      }
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(", "));
      } else {
        setError(detail || `${isAddingWord ? 'Adding word' : 'Purchase'} failed. Please try again.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            {isAddingWord ? `Add "${word}"` : `Claim "${word}"`}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Price Display */}
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-600">{isAddingWord ? "Creation Fee" : "Purchase Price"}</p>
            <p className="text-3xl font-bold text-blue-600">${price}</p>
            <p className="text-sm text-gray-600 mt-1">
              Protected for {lockoutText}
            </p>
          </div>

          {/* Owner Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Name
            </label>
            <input
              type="text"
              value={ownerName}
              onChange={(e) => setOwnerName(e.target.value)}
              maxLength={100}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your name"
            />
          </div>

          {/* Owner Message */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Message (Max 140 characters)
            </label>
            <textarea
              value={ownerMessage}
              onChange={(e) => setOwnerMessage(e.target.value)}
              maxLength={140}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Leave your mark..."
            />
            <p className="text-xs text-gray-500 mt-1">
              {ownerMessage.length}/140 characters
            </p>
          </div>

          {/* Mandatory Acknowledgement */}
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="mt-1"
              />
              <span className="text-sm text-gray-700">
                I acknowledge that I am purchasing temporary ownership. My rights
                to this word expire in {lockoutText}, after which it may be
                purchased by another user.
              </span>
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !acknowledged}
              className="flex-1 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? "Processing..." : `Pay $${price}`}
            </button>
          </div>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          Note: Payment integration coming soon. This is a demo purchase.
        </p>
      </div>
    </div>
  );
}
