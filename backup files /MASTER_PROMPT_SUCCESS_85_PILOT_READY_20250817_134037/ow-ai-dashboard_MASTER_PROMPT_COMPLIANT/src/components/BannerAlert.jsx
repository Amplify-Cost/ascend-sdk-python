import React from "react";

const BannerAlert = ({ message, onDismiss, onReview }) => {
  return (
    <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800 p-4 flex justify-between items-center shadow">
      <div>
        <strong>⚠️ High-Risk Detected:</strong> {message}
      </div>
      <div className="flex gap-2">
        {onReview && (
          <button
            onClick={onReview}
            className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600"
          >
            Review Now
          </button>
        )}
        <button
          onClick={onDismiss}
          className="text-yellow-800 underline text-sm"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
};

export default BannerAlert;
