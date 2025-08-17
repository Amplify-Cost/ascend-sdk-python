import React from "react";

const ToastAlert = ({ message }) => {
  return (
    <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-3 rounded shadow-lg z-50 animate-fade-in">
      <strong>High-Risk Alert:</strong> {message}
    </div>
  );
};

export default ToastAlert;
