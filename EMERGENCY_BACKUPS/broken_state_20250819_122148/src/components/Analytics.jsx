import React, { useEffect, useState } from "react";
import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const Analytics = ({ getAuthHeaders }) => {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/logs`, {
           
        });
        const data = await res.json();
        if (Array.isArray(data)) {
          setLogs(data);
        } else {
          setError("Unexpected response format");
        }
      } catch (err) {
        setError(err.message);
      }
    };
    fetchLogs();
  }, [getAuthHeaders]);

  const countByField = (field) =>
    logs.reduce((acc, log) => {
      const key = log[field] || "Unknown";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

  const buildChartData = (dataObj, label) => ({
    labels: Object.keys(dataObj),
    datasets: [
      {
        label,
        data: Object.values(dataObj),
        backgroundColor: [
          "#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#6366F1", "#14B8A6"
        ],
        borderRadius: 6,
        borderSkipped: false,
        barPercentage: 0.6,
      },
    ],
  });

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#374151",
          font: { family: "Inter", size: 12 },
        },
      },
      tooltip: {
        enabled: true,
        bodyFont: { family: "Inter" },
        titleFont: { family: "Inter" },
      },
    },
    animation: {
      duration: 800,
      easing: "easeOutQuart",
    },
    scales: {
      x: {
        ticks: {
          color: "#6B7280",
          font: { family: "Inter", size: 12 },
        },
      },
      y: {
        ticks: {
          color: "#6B7280",
          font: { family: "Inter", size: 12 },
        },
      },
    },
  };

  if (error) return <p className="text-red-500 mt-6 text-center">❌ {error}</p>;
  if (logs.length === 0) {
    return (
      <div className="text-center text-gray-400 mt-12 text-base">
        No logs available to generate analytics yet. Submit agent actions to populate insights.
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
      <div className="bg-white dark:bg-gray-900 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 w-full aspect-square max-w-full overflow-auto">
        <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-white">
          📊 Logs by Risk Level
        </h3>
        <Pie data={buildChartData(countByField("risk_level"), "Risk Level")} options={chartOptions} />
      </div>
      <div className="bg-white dark:bg-gray-900 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 w-full aspect-square max-w-full overflow-auto">
        <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-white">
          📈 Logs by Status
        </h3>
        <Pie data={buildChartData(countByField("status"), "Status")} options={chartOptions} />
      </div>
      <div className="bg-white dark:bg-gray-900 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 w-full h-[350px] md:col-span-2 overflow-auto">
        <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-white">
          🔧 Logs by Tool Name
        </h3>
        <Bar data={buildChartData(countByField("tool_name"), "Tool Usage")} options={chartOptions} />
      </div>
    </div>
  );
};

export default Analytics;
