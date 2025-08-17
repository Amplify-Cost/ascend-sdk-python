import React from "react";
import frameworkMapping from "../frameworkMapping";

const Compliance = () => {
  return (
    <div className="bg-white p-6 rounded shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Compliance & Framework Mapping</h2>

      <div className="space-y-6">
        {frameworkMapping.map((framework, idx) => (
          <div key={idx}>
            <h3 className="text-xl font-semibold mb-2">{framework.framework}</h3>
            <p className="text-gray-600 mb-4">{framework.description}</p>

            <table className="w-full border text-sm mb-8">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-2 border text-left">Control</th>
                  <th className="p-2 border text-left">Mapped Feature in OW-AI</th>
                </tr>
              </thead>
              <tbody>
                {framework.controls.map((control, i) => (
                  <tr key={i}>
                    <td className="border p-2">{control.control}</td>
                    <td className="border p-2">{control.feature}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Compliance;
