"use client";

import { useState, useEffect } from "react";
import { loadStripe, StripeElementsOptions } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";
import PaymentForm from "./PaymentForm";
import axios from "axios";

// Load Stripe
const stripeKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "";
const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
console.log("Stripe publishable key loaded:", stripeKey ? `${stripeKey.substring(0, 20)}...` : "MISSING");
const stripePromise = loadStripe(stripeKey);

interface PurchaseModalProps {
  word: string;
  price: string;
  isAddingWord?: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PurchaseModalWithPayment({
  word,
  price,
  isAddingWord = false,
  onClose,
  onSuccess,
}: PurchaseModalProps) {
  const [step, setStep] = useState<"details" | "payment">("details");
  const [ownerName, setOwnerName] = useState("");
  const [ownerMessage, setOwnerMessage] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
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

    return null;
  };

  const handleContinueToPayment = async () => {
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

    // Validate content (frontend checks)
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

    // Validate content with backend (profanity & toxicity check)
    setLoading(true);
    try {
      console.log("Validating content...");
      const validationResponse = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/words/validate-content`,
        {
          owner_name: ownerName,
          owner_message: ownerMessage
        }
      );

      if (!validationResponse.data.valid) {
        setError(validationResponse.data.error || "Content validation failed");
        setLoading(false);
        return;
      }

      console.log("Content validated successfully");
    } catch (err: any) {
      console.error("Content validation failed:", err);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(", "));
      } else {
        setError(detail || "Content validation failed");
      }
      setLoading(false);
      return;
    }

    // Create payment intent (only after validation passes)
    try {
      console.log("Creating payment intent for:", word, "isAddingWord:", isAddingWord);
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/payment/create-intent`,
        null,
        {
          params: {
            word_text: word,
            is_new_word: isAddingWord
          }
        }
      );

      console.log("Payment intent created:", response.data);
      setClientSecret(response.data.client_secret);
      setStep("payment");
    } catch (err: any) {
      console.error("Failed to create payment intent:", err);
      console.error("Error response:", err.response?.data);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        // Handle FastAPI validation errors
        setError(detail.map((e: any) => e.msg).join(", "));
      } else {
        setError(detail || "Failed to initialize payment");
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = () => {
    onSuccess();
  };

  const handlePaymentError = (error: string) => {
    setError(error);
  };

  const stripeOptions: StripeElementsOptions = clientSecret ? {
    clientSecret,
    appearance: {
      theme: "stripe",
    },
  } : {};

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
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

        {step === "details" ? (
          /* Step 1: Enter Details */
          <div>
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
                onClick={handleContinueToPayment}
                disabled={loading || !acknowledged}
                className="flex-1 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? "Loading..." : "Continue to Payment"}
              </button>
            </div>
          </div>
        ) : (
          /* Step 2: Payment */
          <div>
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">Payment Amount</p>
              <p className="text-2xl font-bold text-blue-600">${price}</p>
            </div>

            {clientSecret && (
              <Elements stripe={stripePromise} options={stripeOptions}>
                <PaymentForm
                  word={word}
                  price={price}
                  ownerName={ownerName}
                  ownerMessage={ownerMessage}
                  isAddingWord={isAddingWord}
                  onSuccess={handlePaymentSuccess}
                  onError={handlePaymentError}
                />
              </Elements>
            )}

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <button
              onClick={() => setStep("details")}
              className="mt-4 text-sm text-gray-600 hover:text-gray-800"
            >
              ← Back to details
            </button>
          </div>
        )}

        <p className="text-xs text-gray-500 text-center mt-4">
          Powered by Stripe
          {isDemoMode && ". Test with card: 4242 4242 4242 4242"}
        </p>
      </div>
    </div>
  );
}
