const frameworkMapping = [
    {
      framework: "NIST AI RMF",
      description: "Mapping Ascend activities to NIST AI Risk Management Framework categories.",
      controls: [
        { control: "Data Provenance", feature: "Logs agent actions with timestamps" },
        { control: "Access Control", feature: "JWT token-based authentication" },
        { control: "Monitoring", feature: "Tracks status and audit history of agent actions" },
      ],
    },
    {
      framework: "MITRE ATLAS",
      description: "Alignment with MITRE Adversarial Threat Landscape for Artificial-Intelligence Systems.",
      controls: [
        { control: "Telemetry Tampering", feature: "Audit trails capture all changes" },
        { control: "Model Misuse Detection", feature: "Risk-based auto-approval rules" },
      ],
    },
    {
      framework: "OWASP Top 10 LLM Risks",
      description: "Security and governance mappings against OWASP LLM threats.",
      controls: [
        { control: "A01: Prompt Injection", feature: "Action descriptions logged for review" },
        { control: "A06: Sensitive Information Disclosure", feature: "Role-based data access control" },
      ],
    },
  ];
  
  export default frameworkMapping;
  