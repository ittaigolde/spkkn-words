"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getSetupInfo, SetupInfo } from "@/lib/adminApi";

export default function AdminSetupPage() {
  const [setupInfo, setSetupInfo] = useState<SetupInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadSetupInfo();
  }, []);

  const loadSetupInfo = async () => {
    try {
      const info = await getSetupInfo();
      setSetupInfo(info);
      setError(null);
    } catch (err: any) {
      const errorMessage = err.message || "Failed to load setup information";

      // Check if setup is disabled
      if (errorMessage.includes("disabled") || errorMessage.includes("403")) {
        setError("SETUP_DISABLED");
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading setup information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    // Special message for disabled setup
    if (error === "SETUP_DISABLED") {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mx-auto mb-4">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-center text-gray-900 mb-2">Setup Disabled</h2>
            <p className="text-gray-700 text-center mb-4">
              The admin setup page has been disabled for security. This is normal in production.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-800 mb-2">
                <strong>Already set up?</strong>
              </p>
              <p className="text-sm text-blue-800">
                Use your Google Authenticator app to log in at the admin login page.
              </p>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-700 mb-2">
                <strong>Need to re-enable setup?</strong>
              </p>
              <p className="text-sm text-gray-700">
                Set <code className="bg-gray-200 px-1 py-0.5 rounded">ADMIN_SETUP_ENABLED=True</code> in your backend .env file
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => window.location.href = "/admin/login"}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Go to Login
              </button>
              <button
                onClick={() => window.location.href = "/"}
                className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Regular error message
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mx-auto mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-center text-gray-900 mb-2">Setup Error</h2>
          <p className="text-gray-700 text-center mb-4">{error}</p>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-yellow-800">
              Make sure ADMIN_TOTP_SECRET is configured in your backend .env file.
            </p>
          </div>
          <button
            onClick={() => window.location.href = "/"}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  if (!setupInfo) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Warning Banner */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700 font-semibold">
                Security Warning: Disable this page in production!
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                This page exposes your TOTP secret. After setup, disable the /api/admin/setup endpoint or protect it with IP whitelisting.
              </p>
            </div>
          </div>
        </div>

        {/* Main Setup Card */}
        <div className="bg-white rounded-lg shadow-xl overflow-hidden">
          <div className="px-6 py-8 bg-gradient-to-r from-blue-600 to-blue-700">
            <h1 className="text-3xl font-bold text-white text-center">
              Admin TOTP Setup
            </h1>
            <p className="text-blue-100 text-center mt-2">
              Configure Google Authenticator for secure admin access
            </p>
          </div>

          <div className="p-8">
            {/* Step-by-step Instructions */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Setup Instructions</h2>
              <ol className="space-y-3">
                <li className="flex items-start">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold flex-shrink-0">
                    1
                  </span>
                  <span className="ml-3 text-gray-700">
                    Install <strong>Google Authenticator</strong> (or any TOTP app) on your phone
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold flex-shrink-0">
                    2
                  </span>
                  <span className="ml-3 text-gray-700">
                    Open the app and tap <strong>&quot;Scan QR code&quot;</strong> or <strong>&quot;Add account&quot;</strong>
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold flex-shrink-0">
                    3
                  </span>
                  <span className="ml-3 text-gray-700">
                    Scan the QR code below (or enter the secret manually)
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold flex-shrink-0">
                    4
                  </span>
                  <span className="ml-3 text-gray-700">
                    Test the setup by logging in at <strong>/admin/login</strong>
                  </span>
                </li>
              </ol>
            </div>

            {/* QR Code Section */}
            <div className="bg-gray-50 rounded-lg p-8 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-4">
                Scan this QR Code
              </h3>
              <div className="flex justify-center">
                <div className="bg-white p-4 rounded-lg shadow-sm">
                  <img
                    src={setupInfo.qr_code}
                    alt="TOTP QR Code"
                    className="w-64 h-64"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-600 text-center mt-4">
                Account: <strong>Word Registry Admin</strong>
              </p>
            </div>

            {/* Manual Entry Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can&apos;t scan? Manual entry
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                If you can&apos;t scan the QR code, enter this secret key manually in your authenticator app:
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white px-4 py-3 rounded border border-blue-300 font-mono text-sm break-all">
                  {setupInfo.manual_entry}
                </code>
                <button
                  onClick={() => copyToClipboard(setupInfo.manual_entry)}
                  className="px-4 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex-shrink-0"
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-600 mt-2">
                Account name: Word Registry Admin | Time based: Yes
              </p>
            </div>

            {/* Important Notes */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Important Notes</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Codes refresh every 30 seconds
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Make sure your device time is synchronized
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Save the secret key in a password manager as backup
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Never share the secret key or QR code with anyone
                </li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="/admin/login"
                className="flex-1 py-3 bg-blue-600 text-white text-center font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                Go to Login
              </a>
              <Link
                href="/"
                className="flex-1 py-3 border border-gray-300 text-gray-700 text-center font-semibold rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back to Home
              </Link>
            </div>

            {/* Security Reminder */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-xs text-gray-500 text-center">
                🔒 Keep your secret key secure. If compromised, generate a new one and update your .env file.
              </p>
            </div>
          </div>
        </div>

        {/* Setup Complete Checklist */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Setup Complete Checklist</h3>
          <div className="space-y-2">
            <label className="flex items-center">
              <input type="checkbox" className="mr-3 w-4 h-4" />
              <span className="text-gray-700">Google Authenticator installed on phone</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-3 w-4 h-4" />
              <span className="text-gray-700">QR code scanned (or secret entered manually)</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-3 w-4 h-4" />
              <span className="text-gray-700">Secret key saved in password manager</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-3 w-4 h-4" />
              <span className="text-gray-700">Successfully logged in at /admin/login</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-3 w-4 h-4" />
              <span className="text-gray-700">Disabled /api/admin/setup endpoint (production only)</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
