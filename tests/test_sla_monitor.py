"""
Unit tests for SLA Monitor Service
Tests escalation logic, overdue detection, and audit trail
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from services.sla_monitor import SLAMonitor
from models import AgentAction


class TestSLAMonitor:
    """Test suite for SLA Monitor background job"""
    
    @pytest.fixture
    def sla_monitor(self):
        """Create SLA Monitor instance for tests"""
        return SLAMonitor()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        db.query = Mock()
        return db
    
    @pytest.fixture
    def overdue_action(self):
        """Create mock overdue action"""
        action = Mock(spec=AgentAction)
        action.id = 123
        action.sla_deadline = datetime.now(timezone.utc) - timedelta(hours=2)
        action.workflow_stage = 'stage_1'
        action.current_approval_level = 0
        action.required_approval_level = 2
        action.approval_chain = []
        return action
    
    @pytest.fixture
    def max_level_action(self):
        """Create mock action at maximum approval level"""
        action = Mock(spec=AgentAction)
        action.id = 456
        action.sla_deadline = datetime.now(timezone.utc) - timedelta(hours=5)
        action.workflow_stage = 'stage_2'
        action.current_approval_level = 2
        action.required_approval_level = 2
        action.approval_chain = []
        return action

    def test_find_overdue_workflows(self, sla_monitor, mock_db):
        """Test finding overdue workflows"""
        # Create mock actions with proper datetime attributes
        mock_action1 = Mock(spec=AgentAction)
        mock_action1.id = 1
        mock_action1.sla_deadline = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_action1.workflow_stage = 'stage_1'
        
        mock_action2 = Mock(spec=AgentAction)
        mock_action2.id = 2
        mock_action2.sla_deadline = datetime.now(timezone.utc) - timedelta(hours=2)
        mock_action2.workflow_stage = 'stage_2'
        
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [mock_action1, mock_action2]
        
        result = sla_monitor.find_overdue_workflows(mock_db)
        
        assert len(result) == 2
        mock_db.query.assert_called_once_with(AgentAction)

    def test_escalate_approval_level(self, sla_monitor, overdue_action, mock_db):
        """Test escalation increases approval level"""
        result = sla_monitor._escalate_approval_level(overdue_action, mock_db)
        
        assert result == 'escalated'
        assert overdue_action.current_approval_level == 1
        assert overdue_action.workflow_stage == 'stage_1'

    def test_send_executive_alert(self, sla_monitor, max_level_action, mock_db):
        """Test executive alert sent at max level"""
        result = sla_monitor._send_executive_alert(max_level_action, mock_db)
        
        assert result == 'alerted'
        assert len(max_level_action.approval_chain) > 0

    def test_escalate_workflow(self, sla_monitor, overdue_action, mock_db):
        """Test escalate workflow logic"""
        result = sla_monitor.escalate_workflow(overdue_action, mock_db)
        assert result == 'escalated'

    def test_recently_escalated(self, sla_monitor):
        """Test duplicate escalation prevention"""
        action = Mock(spec=AgentAction)
        action.id = 999
        action.approval_chain = [{
            'event_type': 'sla_escalation',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }]
        
        result = sla_monitor._recently_escalated(action)
        assert result is True

    def test_run_check_no_overdue(self, sla_monitor, mock_db):
        """Test run check with no overdue workflows"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        
        result = sla_monitor.run_check(mock_db)
        
        assert result == {'overdue': 0, 'escalated': 0, 'alerted': 0}

    def test_get_sla_metrics(self, sla_monitor, mock_db):
        """Test SLA metrics calculation"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.count.side_effect = [10, 2, 3, 5]
        
        result = sla_monitor.get_sla_metrics(mock_db)
        
        assert result['total_workflows'] == 10
        assert result['overdue'] == 2
        assert result['compliance_rate'] == 80.0
