import React, { useEffect, useState } from "react";

import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';

const RulePerformancePanel = ({ getAuthHeaders }) => {
  const [performance, setPerformance] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/rules/performance`, {
          headers: await getAuthHeaders(),
        });
        const data = await res.json();
        setPerformance(data.performance || {});
      } catch (err) {
        logger.error("Error fetching rule performance:", err);
        setError("Failed to load rule performance.");
      } finally {
        setLoading(false);
      }
    };

    fetchPerformance();
  }, [getAuthHeaders]);

  if (loading) return <div className="p-4">Loading rule performance...</div>;
  if (error) return <div className="p-4 text-red-500">{error}</div>;

  return (
    <div className="p-4 bg-white rounded-2xl shadow-md mt-4">
      <h2 className="text-xl font-semibold mb-3">Rule Performance Summary</h2>
      <table className="w-full table-auto border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="px-4 py-2 border">Rule ID</th>
            <th className="px-4 py-2 border">Correct Matches</th>
            <th className="px-4 py-2 border">False Positives</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(performance).map(([ruleId, stats]) => (
            <tr key={ruleId} className="border-t">
              <td className="px-4 py-2 border">{ruleId}</td>
              <td className="px-4 py-2 border text-green-600 font-medium">{stats.correct}</td>
              <td className="px-4 py-2 border text-red-500 font-medium">{stats.false_positive}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RulePerformancePanel;
