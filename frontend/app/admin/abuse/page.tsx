"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  getReportedMessages,
  moderateMessage,
  adminLogout,
  adminTokenStorage,
  ReportedMessage,
  ReportedMessagesResponse,
} from "@/lib/adminApi";

export default function AdminAbusePage() {
  const router = useRouter();
  const [data, setData] = useState<ReportedMessagesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    // Check if user is authenticated
    if (!adminTokenStorage.get()) {
      router.push("/admin/login");
      return;
    }

    loadReportedMessages();
  }, [router, currentPage]);

  const loadReportedMessages = async () => {
    try {
      setLoading(true);
      const result = await getReportedMessages(currentPage, pageSize);
      setData(result);
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

  const handleModerate = async (wordId: number, action: 'approve' | 'reject' | 'protect') => {
    setProcessingId(wordId);
    try {
      await moderateMessage(wordId, action);
      await loadReportedMessages();
    } catch (err: any) {
      alert(`Failed to ${action} message: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handleLogout = () => {
    adminLogout();
    router.push("/admin/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-center text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Content Moderation</h1>
            <p className="text-gray-600 mt-1">Review and moderate reported messages</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => router.push("/admin/dashboard")}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Dashboard
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Reported Messages */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Reported Messages ({data?.total || 0} total)
            </h2>
            {data && data.total > 0 && (
              <p className="text-sm text-gray-600 mt-1">
                Page {data.page} of {data.total_pages}
              </p>
            )}
          </div>

          {!data || data.messages.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No reported messages
            </div>
          ) : (
            <>
              <div className="divide-y divide-gray-200">
                {data.messages.map((msg) => (
                <div key={msg.word_id} className="p-6 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-gray-900">{msg.word_text}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          msg.moderation_status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : msg.moderation_status === 'approved'
                            ? 'bg-green-100 text-green-800'
                            : msg.moderation_status === 'rejected'
                            ? 'bg-red-100 text-red-800'
                            : msg.moderation_status === 'protected'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {msg.moderation_status || 'Unmoderated'}
                        </span>
                        <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                          {msg.report_count} report{msg.report_count !== 1 ? 's' : ''}
                        </span>
                      </div>

                      <div className="mb-3">
                        <p className="text-sm text-gray-600">
                          Owner: <span className="font-medium">{msg.owner_name || 'None'}</span>
                        </p>
                        <p className="text-sm text-gray-600">
                          Updated: {new Date(msg.updated_at).toLocaleString()}
                        </p>
                        {msg.moderated_at && (
                          <p className="text-sm text-gray-600">
                            Moderated: {new Date(msg.moderated_at).toLocaleString()}
                          </p>
                        )}
                      </div>

                      {msg.owner_message && (
                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                          <p className="text-sm font-semibold text-gray-700 mb-1">Message:</p>
                          <p className="text-gray-900 italic">&quot;{msg.owner_message}&quot;</p>
                        </div>
                      )}
                    </div>

                    {!msg.moderation_status ? (
                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => handleModerate(msg.word_id, 'protect')}
                          disabled={processingId === msg.word_id}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 whitespace-nowrap"
                          title="Protect from future reports and reset countdown"
                        >
                          {processingId === msg.word_id ? 'Processing...' : 'Protect'}
                        </button>
                        <button
                          onClick={() => handleModerate(msg.word_id, 'approve')}
                          disabled={processingId === msg.word_id}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                        >
                          {processingId === msg.word_id ? 'Processing...' : 'Approve'}
                        </button>
                        <button
                          onClick={() => handleModerate(msg.word_id, 'reject')}
                          disabled={processingId === msg.word_id}
                          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
                        >
                          {processingId === msg.word_id ? 'Processing...' : 'Reject'}
                        </button>
                      </div>
                    ) : (
                      <div className="ml-4 text-sm text-gray-500">
                        {msg.moderation_status === 'protected' ? 'Protected ✓' : 'Already moderated'}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {currentPage} of {data.total_pages}
                  </span>
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === data.total_pages}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
