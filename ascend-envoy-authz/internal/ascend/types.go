// Package ascend provides the ASCEND Platform API client.
//
// Author: ASCEND Platform Engineering
package ascend

// Action represents an action to submit to ASCEND for governance evaluation.
type Action struct {
	AgentID         string                 `json:"agent_id"`
	ActionType      string                 `json:"action_type"`
	ToolName        string                 `json:"tool_name,omitempty"`
	Description     string                 `json:"description,omitempty"`
	ResourceType    string                 `json:"resource_type,omitempty"`
	TargetSystem    string                 `json:"target_system,omitempty"`
	Environment     string                 `json:"environment,omitempty"`
	DataSensitivity string                 `json:"data_sensitivity,omitempty"`
	Context         map[string]interface{} `json:"context,omitempty"`
}

// Decision represents the ASCEND Platform's governance decision.
type Decision struct {
	// Core fields
	ActionID int64  `json:"id"`
	Status   string `json:"status"` // approved, pending_approval, denied

	// Risk assessment
	RiskScore float64 `json:"risk_score"`
	RiskLevel string  `json:"risk_level"` // low, medium, high, critical

	// Additional details
	RequiresApproval bool   `json:"requires_approval"`
	AlertTriggered   bool   `json:"alert_triggered"`
	Message          string `json:"message,omitempty"`
	DenialReason     string `json:"denial_reason,omitempty"`

	// Workflow (if pending)
	WorkflowID int64 `json:"workflow_id,omitempty"`

	// Correlation
	CorrelationID string `json:"correlation_id,omitempty"`
}

// IsApproved returns true if the action was approved.
func (d *Decision) IsApproved() bool {
	return d.Status == StatusApproved
}

// IsPending returns true if the action requires human approval.
func (d *Decision) IsPending() bool {
	return d.Status == StatusPending
}

// IsDenied returns true if the action was denied.
func (d *Decision) IsDenied() bool {
	return d.Status == StatusDenied
}

// Status constants
const (
	StatusApproved = "approved"
	StatusPending  = "pending_approval"
	StatusDenied   = "denied"
)

// Risk level constants
const (
	RiskLow      = "low"
	RiskMedium   = "medium"
	RiskHigh     = "high"
	RiskCritical = "critical"
)
