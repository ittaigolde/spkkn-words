"use client";

import { useState, useEffect } from "react";
import {
  PaymentElement,
  useStripe,
  useElements
} from "@stripe/react-stripe-js";
import axios from "axios";

interface PaymentFormProps {
  word: string;
  price: string;
  ownerName: string;
  ownerMessage: string;
  isAddingWord: boolean;
  onSuccess: () => void;
  onError: (error: string) => void;
}

export default function PaymentForm({
  word,
  price,
  ownerName,
  ownerMessage,
  isAddingWord,
  onSuccess,
  onError
}: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();

  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || isProcessing) {
      return;
    }

    setIsProcessing(true);
    setMessage("");

    try {
      // Confirm the payment
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment-success`,
        },
        redirect: "if_required",
      });

      if (error) {
        console.error("Stripe payment error:", error);
        console.error("Error type:", error.type);
        console.error("Error code:", error.code);

        // Handle the case where payment already succeeded but we're trying to confirm again
        if (error.code === "payment_intent_unexpected_state" && error.payment_intent?.status === "succeeded") {
          // Payment already succeeded, just proceed with confirmation
          try {
            await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/payment/confirm-purchase`, {
              payment_intent_id: error.payment_intent.id,
              word_text: word,
              owner_name: ownerName,
              owner_message: ownerMessage,
              is_new_word: isAddingWord
            });
            onSuccess();
            return;
          } catch (confirmErr: any) {
            const detail = confirmErr.response?.data?.detail;
            if (Array.isArray(detail)) {
              onError(detail.map((e: any) => e.msg).join(", "));
            } else {
              onError(detail || "Purchase confirmation failed");
            }
            setIsProcessing(false);
            return;
          }
        }

        setMessage(error.message || "An error occurred");
        onError(error.message || "Payment failed");
        setIsProcessing(false);
      } else if (paymentIntent && paymentIntent.status === "succeeded") {
        // Payment succeeded, confirm purchase with backend
        try {
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/payment/confirm-purchase`, {
            payment_intent_id: paymentIntent.id,
            word_text: word,
            owner_name: ownerName,
            owner_message: ownerMessage,
            is_new_word: isAddingWord
          });

          onSuccess();
        } catch (err: any) {
          const detail = err.response?.data?.detail;
          if (Array.isArray(detail)) {
            onError(detail.map((e: any) => e.msg).join(", "));
          } else {
            onError(detail || "Purchase confirmation failed");
          }
          setIsProcessing(false);
        }
      }
    } catch (unexpectedError: any) {
      console.error("Unexpected error during payment:", unexpectedError);
      setMessage("An unexpected error occurred");
      onError("An unexpected error occurred");
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PaymentElement />

      {message && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{message}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || isProcessing}
        className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isProcessing ? "Processing..." : `Pay $${price}`}
      </button>
    </form>
  );
}
