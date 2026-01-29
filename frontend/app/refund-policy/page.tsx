import Link from "next/link";

export default function RefundPolicyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Refund & Return Policy
        </h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            <strong>Effective Date:</strong> January 29, 2026
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Overview
            </h2>
            <p className="text-gray-700 leading-relaxed">
              The Word Registry offers digital word ownership rights that are delivered instantly upon purchase.
              Due to the immediate and digital nature of our service, all sales are final.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              No Refunds or Returns
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              All purchases made on The Word Registry are <strong>final and non-refundable</strong>.
              This policy exists because:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Word ownership rights are granted immediately upon successful payment</li>
              <li>You receive instant access to claim and customize your word</li>
              <li>The service is delivered in full at the time of purchase</li>
              <li>Our platform operates as a competitive marketplace where word availability changes in real-time</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Temporary Ownership
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Please note that word ownership in The Word Registry is <strong>temporary</strong>.
              After your lockout period expires (1 hour per dollar spent), your word becomes available
              for other users to purchase. This is a core feature of our service and not grounds for a refund.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Payment Processing Errors
            </h2>
            <p className="text-gray-700 leading-relaxed">
              If you were charged but did not receive word ownership due to a technical error,
              please contact us immediately at{" "}
              <a
                href="mailto:team@spkkn.com"
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                team@spkkn.com
              </a>
              . We will investigate and resolve the issue promptly.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Disputes and Questions
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have questions about a purchase or wish to dispute a charge, please contact us at:
            </p>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-900 font-medium">Email:</p>
              <a
                href="mailto:team@spkkn.com"
                className="text-indigo-600 hover:text-indigo-700 text-lg font-semibold"
              >
                team@spkkn.com
              </a>
            </div>
            <p className="text-gray-700 leading-relaxed mt-4">
              We aim to respond to all inquiries within 48 hours. Please include:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Your order/transaction ID</li>
              <li>The word you purchased</li>
              <li>A detailed description of the issue</li>
              <li>Any relevant screenshots or documentation</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Unauthorized Charges
            </h2>
            <p className="text-gray-700 leading-relaxed">
              If you believe a charge was made without your authorization, please contact your bank
              or credit card company immediately and then notify us at{" "}
              <a
                href="mailto:team@spkkn.com"
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                team@spkkn.com
              </a>
              . We take payment security seriously and will investigate any reports of unauthorized transactions.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Understanding Before Purchase
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Before making a purchase, please ensure you understand:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>The word price and lockout duration</li>
              <li>That ownership is temporary and will expire</li>
              <li>That other users can purchase your word after the lockout period</li>
              <li>All sales are final with no refunds or returns</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Policy Updates
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to update this refund policy at any time. Any changes will be
              posted on this page with an updated effective date. Your continued use of The Word
              Registry after policy changes constitutes acceptance of the updated terms.
            </p>
          </section>

          <div className="border-t border-gray-200 pt-6 mt-8">
            <p className="text-sm text-gray-600">
              For any questions about this policy, please contact us at{" "}
              <a
                href="mailto:team@spkkn.com"
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                team@spkkn.com
              </a>
            </p>
          </div>

          <div className="mt-8">
            <Link
              href="/"
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
