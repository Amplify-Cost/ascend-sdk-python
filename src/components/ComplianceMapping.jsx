import React from 'react';
import { Shield, CheckCircle, AlertCircle } from 'lucide-react';

export const ComplianceMapping = ({ policies }) => {
  const frameworks = [
    {
      name: 'NIST 800-53',
      controls: [
        { id: 'AC-3', name: 'Access Enforcement', covered: true },
        { id: 'AC-6', name: 'Least Privilege', covered: true },
        { id: 'AU-2', name: 'Audit Events', covered: true },
        { id: 'SI-4', name: 'Information System Monitoring', covered: false }
      ]
    },
    {
      name: 'SOC 2',
      controls: [
        { id: 'CC6.1', name: 'Logical Access Controls', covered: true },
        { id: 'CC6.2', name: 'System Operations', covered: true },
        { id: 'CC7.2', name: 'System Monitoring', covered: true },
        { id: 'CC6.3', name: 'Access Review', covered: false }
      ]
    },
    {
      name: 'ISO 27001',
      controls: [
        { id: 'A.9.2', name: 'User Access Management', covered: true },
        { id: 'A.9.4', name: 'System Access Control', covered: true },
        { id: 'A.12.4', name: 'Logging and Monitoring', covered: true },
        { id: 'A.18.1', name: 'Compliance', covered: false }
      ]
    }
  ];

  const calculateCoverage = (controls) => {
    const covered = controls.filter(c => c.covered).length;
    return ((covered / controls.length) * 100).toFixed(0);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-6 w-6 text-purple-600" />
        <h3 className="text-2xl font-bold">Compliance Framework Coverage</h3>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">Policy-to-Compliance Mapping</p>
            <p className="text-sm text-blue-700 mt-1">
              Your {policies.length} active policies provide coverage for multiple compliance frameworks.
              Review gaps below to ensure full compliance.
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        {frameworks.map((framework) => {
          const coverage = calculateCoverage(framework.controls);
          return (
            <div key={framework.name} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold">{framework.name}</h4>
                <div className="flex items-center gap-2">
                  <div className="text-2xl font-bold text-blue-600">{coverage}%</div>
                  <span className="text-sm text-gray-600">Coverage</span>
                </div>
              </div>

              <div className="mb-4">
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-500 h-3 rounded-full transition-all"
                    style={{ width: `${coverage}%` }}
                  />
                </div>
              </div>

              <div className="space-y-2">
                {framework.controls.map((control) => (
                  <div
                    key={control.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {control.covered ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                      )}
                      <div>
                        <div className="font-medium text-sm">{control.id}</div>
                        <div className="text-sm text-gray-600">{control.name}</div>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      control.covered
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {control.covered ? 'Covered' : 'Gap'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ComplianceMapping;
