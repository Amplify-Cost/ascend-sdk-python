#!/usr/bin/env python3
"""
Policy Engine Performance Validation Script - Phase 1.2

This script validates that the real-time policy evaluation engine meets
the sub-200ms performance requirements across different scenarios.

Usage: python validate_policy_engine_performance.py
"""

import asyncio
import time
import statistics
from datetime import datetime, UTC
from typing import List, Dict, Any
import sys
import os

# Add current directory to path for imports
sys.path.append('.')

from policy_engine import (
    EnterpriseRealTimePolicyEngine,
    create_policy_engine,
    create_evaluation_context,
    PolicyDecision,
    RiskCategory,
    NaturalLanguageParser
)
from database import SessionLocal
from models_mcp_governance import MCPPolicy


class PolicyEngineValidator:
    """Comprehensive policy engine performance validator."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.policy_engine = None
        self.test_results = []
        
    async def setup_test_environment(self):
        """Setup test environment with sample policies."""
        print("🔧 Setting up test environment...")
        
        try:
            self.policy_engine = create_policy_engine(self.db)
            print("✅ Policy engine created successfully")
            
            # Create sample test policies
            await self._create_test_policies()
            print("✅ Test policies created")
            
        except Exception as e:
            print(f"❌ Test environment setup failed: {e}")
            return False
        
        return True
    
    async def _create_test_policies(self):
        """Create sample policies for testing."""
        test_policies = [
            {
                'policy_name': 'High Risk File Access Policy',
                'natural_language_description': 'Block access to sensitive customer data files in production',
                'action': 'DENY',
                'resource_patterns': ['*/customer_data/*', '*/sensitive/*'],
                'namespace_patterns': ['database', 'filesystem'],
                'verb_patterns': ['read', 'write', 'access'],
                'priority': 100
            },
            {
                'policy_name': 'Admin Access Policy', 
                'natural_language_description': 'Require approval for admin operations',
                'action': 'REQUIRE_APPROVAL',
                'resource_patterns': ['/admin/*'],
                'namespace_patterns': ['administration'],
                'verb_patterns': ['*'],
                'priority': 90
            },
            {
                'policy_name': 'Low Risk Monitoring Policy',
                'natural_language_description': 'Allow health checks and monitoring',
                'action': 'ALLOW',
                'resource_patterns': ['/health', '/status', '/metrics'],
                'namespace_patterns': ['monitoring'],
                'verb_patterns': ['read'],
                'priority': 80
            }
        ]
        
        for policy_data in test_policies:
            try:
                # Check if policy already exists
                existing = self.db.query(MCPPolicy).filter(
                    MCPPolicy.policy_name == policy_data['policy_name']
                ).first()
                
                if not existing:
                    policy = MCPPolicy(
                        policy_name=policy_data['policy_name'],
                        policy_description=policy_data['natural_language_description'],
                        natural_language_description=policy_data['natural_language_description'],
                        policy_status='deployed',
                        is_active=True,
                        action=policy_data['action'],
                        resource_patterns=policy_data['resource_patterns'],
                        namespace_patterns=policy_data['namespace_patterns'],
                        verb_patterns=policy_data['verb_patterns'],
                        priority=policy_data['priority'],
                        created_by='test_system',
                        major_version=1,
                        minor_version=0,
                        patch_version=0
                    )
                    
                    self.db.add(policy)
                    self.db.commit()
                    print(f"   📋 Created policy: {policy_data['policy_name']}")
                else:
                    print(f"   📋 Policy exists: {policy_data['policy_name']}")
                    
            except Exception as e:
                print(f"   ❌ Failed to create policy {policy_data['policy_name']}: {e}")
                self.db.rollback()
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance validation tests."""
        print("\n🚀 Starting performance validation tests...")
        
        test_scenarios = [
            {
                'name': 'High Risk Database Access',
                'context': create_evaluation_context(
                    user_id='test_user_001',
                    user_email='analyst@company.com',
                    user_role='analyst',
                    action_type='database_query',
                    resource='/database/customer_data/users.table',
                    namespace='database',
                    environment='production'
                ),
                'expected_decision': PolicyDecision.DENY,
                'target_performance_ms': 200
            },
            {
                'name': 'Admin User Management',
                'context': create_evaluation_context(
                    user_id='admin_user_001',
                    user_email='admin@company.com',
                    user_role='admin',
                    action_type='user_create',
                    resource='/admin/users/create',
                    namespace='administration',
                    environment='production'
                ),
                'expected_decision': PolicyDecision.REQUIRE_APPROVAL,
                'target_performance_ms': 200
            },
            {
                'name': 'System Health Check',
                'context': create_evaluation_context(
                    user_id='monitoring_service',
                    user_email='monitoring@company.com',
                    user_role='service',
                    action_type='health_check',
                    resource='/health/status',
                    namespace='monitoring',
                    environment='production'
                ),
                'expected_decision': PolicyDecision.ALLOW,
                'target_performance_ms': 200
            },
            {
                'name': 'File System Access',
                'context': create_evaluation_context(
                    user_id='developer_001',
                    user_email='dev@company.com',
                    user_role='developer',
                    action_type='file_read',
                    resource='/app/logs/debug.log',
                    namespace='filesystem',
                    environment='development'
                ),
                'expected_decision': PolicyDecision.REQUIRE_APPROVAL,
                'target_performance_ms': 200
            },
            {
                'name': 'Bulk Operations Test',
                'context': create_evaluation_context(
                    user_id='batch_processor',
                    user_email='batch@company.com',
                    user_role='service',
                    action_type='bulk_update',
                    resource='/api/bulk/users',
                    namespace='api',
                    environment='production'
                ),
                'expected_decision': PolicyDecision.REQUIRE_APPROVAL,
                'target_performance_ms': 200
            }
        ]
        
        # Run each test scenario multiple times for statistical accuracy
        all_results = []
        
        for scenario in test_scenarios:
            print(f"\n📊 Testing: {scenario['name']}")
            scenario_results = []
            
            # Run each scenario 10 times
            for iteration in range(10):
                try:
                    start_time = time.time()
                    
                    result = await self.policy_engine.evaluate_policy(
                        scenario['context']
                    )
                    
                    end_time = time.time()
                    evaluation_time_ms = (end_time - start_time) * 1000
                    
                    test_result = {
                        'scenario': scenario['name'],
                        'iteration': iteration + 1,
                        'evaluation_time_ms': evaluation_time_ms,
                        'decision': result.decision,
                        'risk_score': result.risk_score.total_score,
                        'risk_level': result.risk_score.risk_level,
                        'cache_hit': result.cache_hit,
                        'matched_policies_count': len(result.matched_policies),
                        'sub_200ms': evaluation_time_ms < 200,
                        'meets_target': evaluation_time_ms < scenario['target_performance_ms'],
                        'expected_decision_met': result.decision == scenario.get('expected_decision'),
                        'success': True
                    }
                    
                    scenario_results.append(test_result)
                    all_results.append(test_result)
                    
                    # Print progress
                    status = "✅" if test_result['sub_200ms'] else "❌"
                    cache_status = "💾" if test_result['cache_hit'] else "🔄"
                    print(f"   {status} Iteration {iteration + 1}: {evaluation_time_ms:.2f}ms {cache_status}")
                    
                except Exception as e:
                    print(f"   ❌ Iteration {iteration + 1} failed: {e}")
                    all_results.append({
                        'scenario': scenario['name'],
                        'iteration': iteration + 1,
                        'error': str(e),
                        'success': False
                    })
            
            # Calculate scenario statistics
            successful_tests = [r for r in scenario_results if r.get('success', False)]
            if successful_tests:
                times = [r['evaluation_time_ms'] for r in successful_tests]
                sub_200ms_count = len([r for r in successful_tests if r['sub_200ms']])
                
                print(f"   📈 Scenario Summary:")
                print(f"      - Average time: {statistics.mean(times):.2f}ms")
                print(f"      - Median time: {statistics.median(times):.2f}ms")
                print(f"      - Min time: {min(times):.2f}ms")
                print(f"      - Max time: {max(times):.2f}ms")
                print(f"      - Sub-200ms rate: {sub_200ms_count}/{len(successful_tests)} ({(sub_200ms_count/len(successful_tests)*100):.1f}%)")
        
        return self._analyze_results(all_results)
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results and generate performance report."""
        print("\n📋 Analyzing performance results...")
        
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]
        
        if not successful_results:
            return {
                'success': False,
                'error': 'No successful test results',
                'total_tests': len(results),
                'failed_tests': len(failed_results)
            }
        
        # Extract performance metrics
        evaluation_times = [r['evaluation_time_ms'] for r in successful_results]
        sub_200ms_results = [r for r in successful_results if r['sub_200ms']]
        cache_hits = [r for r in successful_results if r['cache_hit']]
        
        # Calculate statistics
        performance_stats = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'failed_tests': len(failed_results),
            'success_rate': len(successful_results) / len(results) * 100,
            
            'evaluation_time_stats': {
                'mean_ms': statistics.mean(evaluation_times),
                'median_ms': statistics.median(evaluation_times),
                'min_ms': min(evaluation_times),
                'max_ms': max(evaluation_times),
                'std_dev_ms': statistics.stdev(evaluation_times) if len(evaluation_times) > 1 else 0
            },
            
            'performance_compliance': {
                'sub_200ms_count': len(sub_200ms_results),
                'sub_200ms_rate': len(sub_200ms_results) / len(successful_results) * 100,
                'target_met': len(sub_200ms_results) == len(successful_results)
            },
            
            'caching_performance': {
                'cache_hit_count': len(cache_hits),
                'cache_hit_rate': len(cache_hits) / len(successful_results) * 100
            }
        }
        
        # Risk scoring analysis
        risk_scores = [r['risk_score'] for r in successful_results]
        if risk_scores:
            performance_stats['risk_scoring'] = {
                'mean_score': statistics.mean(risk_scores),
                'score_distribution': {
                    'low_risk_count': len([s for s in risk_scores if s < 40]),
                    'medium_risk_count': len([s for s in risk_scores if 40 <= s < 70]),
                    'high_risk_count': len([s for s in risk_scores if s >= 70])
                }
            }
        
        # Policy matching analysis
        policy_matches = [r['matched_policies_count'] for r in successful_results]
        if policy_matches:
            performance_stats['policy_matching'] = {
                'mean_matches': statistics.mean(policy_matches),
                'max_matches': max(policy_matches),
                'zero_matches_count': len([m for m in policy_matches if m == 0])
            }
        
        return performance_stats
    
    async def test_natural_language_parsing(self):
        """Test natural language policy parsing performance."""
        print("\n🔤 Testing natural language parsing...")
        
        test_descriptions = [
            "Block access to customer data files in production environment",
            "Require approval for admin operations on user management",
            "Allow read access to monitoring endpoints for health checks",
            "Deny write access to financial data for non-finance users",
            "Escalate high-risk operations to security team for review"
        ]
        
        parsing_results = []
        
        for description in test_descriptions:
            start_time = time.time()
            
            try:
                parsed_rule = NaturalLanguageParser.parse_natural_language_rule(description)
                parsing_time_ms = (time.time() - start_time) * 1000
                
                parsing_results.append({
                    'description': description,
                    'parsing_time_ms': parsing_time_ms,
                    'decision': parsed_rule['decision'],
                    'confidence': parsed_rule['confidence'],
                    'resource_patterns': parsed_rule['resource_patterns'],
                    'risk_factors': parsed_rule['risk_factors'],
                    'success': True
                })
                
                print(f"   ✅ Parsed in {parsing_time_ms:.2f}ms: {description[:50]}...")
                
            except Exception as e:
                parsing_results.append({
                    'description': description,
                    'error': str(e),
                    'success': False
                })
                print(f"   ❌ Failed: {description[:50]}... - {e}")
        
        successful_parses = [r for r in parsing_results if r.get('success', False)]
        if successful_parses:
            parse_times = [r['parsing_time_ms'] for r in successful_parses]
            avg_parse_time = statistics.mean(parse_times)
            print(f"   📊 Average parsing time: {avg_parse_time:.2f}ms")
        
        return parsing_results
    
    async def test_cache_performance(self):
        """Test caching performance and efficiency."""
        print("\n💾 Testing cache performance...")
        
        # Create test context
        test_context = create_evaluation_context(
            user_id='cache_test_user',
            user_email='cache@test.com',
            user_role='user',
            action_type='cache_test',
            resource='/cache/test/resource',
            namespace='testing'
        )
        
        # First evaluation (cache miss)
        print("   🔄 Testing cache miss performance...")
        start_time = time.time()
        result1 = await self.policy_engine.evaluate_policy(test_context)
        miss_time = (time.time() - start_time) * 1000
        
        # Second evaluation (cache hit)
        print("   💾 Testing cache hit performance...")
        start_time = time.time()
        result2 = await self.policy_engine.evaluate_policy(test_context)
        hit_time = (time.time() - start_time) * 1000
        
        cache_performance = {
            'cache_miss_time_ms': miss_time,
            'cache_hit_time_ms': hit_time,
            'cache_speedup_factor': miss_time / max(hit_time, 0.1),
            'cache_efficiency': max(0, (miss_time - hit_time) / miss_time * 100)
        }
        
        print(f"   📊 Cache miss: {miss_time:.2f}ms")
        print(f"   📊 Cache hit: {hit_time:.2f}ms")
        print(f"   📊 Speedup: {cache_performance['cache_speedup_factor']:.2f}x")
        print(f"   📊 Efficiency: {cache_performance['cache_efficiency']:.1f}%")
        
        return cache_performance
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive performance report."""
        
        report_lines = [
            "=" * 80,
            "ENTERPRISE REAL-TIME POLICY ENGINE - PERFORMANCE VALIDATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now(UTC).isoformat()}",
            "",
            "🎯 PERFORMANCE REQUIREMENTS:",
            "   - Sub-200ms policy evaluation response time",
            "   - Enterprise-grade reliability and accuracy",
            "   - Comprehensive risk scoring across 4 categories",
            "   - Efficient caching for repeated evaluations",
            "",
            "📊 TEST RESULTS SUMMARY:",
            f"   Total Tests: {results.get('total_tests', 0)}",
            f"   Successful: {results.get('successful_tests', 0)}",
            f"   Failed: {results.get('failed_tests', 0)}",
            f"   Success Rate: {results.get('success_rate', 0):.1f}%",
            ""
        ]
        
        # Performance metrics
        if 'evaluation_time_stats' in results:
            stats = results['evaluation_time_stats']
            report_lines.extend([
                "⚡ PERFORMANCE METRICS:",
                f"   Average Response Time: {stats['mean_ms']:.2f}ms",
                f"   Median Response Time: {stats['median_ms']:.2f}ms",
                f"   Fastest Response: {stats['min_ms']:.2f}ms",
                f"   Slowest Response: {stats['max_ms']:.2f}ms",
                f"   Standard Deviation: {stats['std_dev_ms']:.2f}ms",
                ""
            ])
        
        # Compliance metrics
        if 'performance_compliance' in results:
            compliance = results['performance_compliance']
            status = "✅ PASSED" if compliance['target_met'] else "❌ FAILED"
            report_lines.extend([
                "🎯 COMPLIANCE STATUS:",
                f"   Sub-200ms Target: {status}",
                f"   Sub-200ms Count: {compliance['sub_200ms_count']}/{results.get('successful_tests', 0)}",
                f"   Compliance Rate: {compliance['sub_200ms_rate']:.1f}%",
                ""
            ])
        
        # Caching performance
        if 'caching_performance' in results:
            caching = results['caching_performance']
            report_lines.extend([
                "💾 CACHING PERFORMANCE:",
                f"   Cache Hit Rate: {caching['cache_hit_rate']:.1f}%",
                f"   Cache Hits: {caching['cache_hit_count']}/{results.get('successful_tests', 0)}",
                ""
            ])
        
        # Risk scoring
        if 'risk_scoring' in results:
            risk = results['risk_scoring']
            report_lines.extend([
                "🛡️  RISK SCORING ANALYSIS:",
                f"   Average Risk Score: {risk['mean_score']:.1f}/100",
                f"   Low Risk (0-39): {risk['score_distribution']['low_risk_count']} tests",
                f"   Medium Risk (40-69): {risk['score_distribution']['medium_risk_count']} tests",
                f"   High Risk (70-100): {risk['score_distribution']['high_risk_count']} tests",
                ""
            ])
        
        # Final assessment
        overall_success = (
            results.get('success_rate', 0) >= 95 and
            results.get('performance_compliance', {}).get('target_met', False)
        )
        
        status_emoji = "✅" if overall_success else "❌"
        status_text = "PASSED" if overall_success else "FAILED"
        
        report_lines.extend([
            "🏆 OVERALL ASSESSMENT:",
            f"   Enterprise Readiness: {status_emoji} {status_text}",
            f"   Performance Target Met: {'✅' if results.get('performance_compliance', {}).get('target_met', False) else '❌'}",
            f"   System Reliability: {'✅' if results.get('success_rate', 0) >= 95 else '❌'}",
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    async def cleanup(self):
        """Cleanup test environment."""
        if self.db:
            self.db.close()


async def main():
    """Main validation function."""
    print("🏢 Enterprise Real-Time Policy Engine - Performance Validation")
    print("=" * 80)
    
    validator = PolicyEngineValidator()
    
    try:
        # Setup test environment
        if not await validator.setup_test_environment():
            print("❌ Failed to setup test environment")
            return
        
        # Run performance tests
        performance_results = await validator.run_performance_tests()
        
        # Test natural language parsing
        nl_results = await validator.test_natural_language_parsing()
        
        # Test cache performance
        cache_results = await validator.test_cache_performance()
        
        # Generate and display report
        if performance_results.get('success', True):
            report = validator.generate_performance_report(performance_results)
            print(f"\n{report}")
            
            # Additional results
            print("\n🔤 NATURAL LANGUAGE PARSING:")
            successful_parses = [r for r in nl_results if r.get('success', False)]
            if successful_parses:
                avg_parse_time = statistics.mean([r['parsing_time_ms'] for r in successful_parses])
                print(f"   Average parsing time: {avg_parse_time:.2f}ms")
                print(f"   Success rate: {len(successful_parses)}/{len(nl_results)} ({len(successful_parses)/len(nl_results)*100:.1f}%)")
            
            print(f"\n💾 CACHE PERFORMANCE:")
            print(f"   Cache miss: {cache_results.get('cache_miss_time_ms', 0):.2f}ms")
            print(f"   Cache hit: {cache_results.get('cache_hit_time_ms', 0):.2f}ms")
            print(f"   Speedup: {cache_results.get('cache_speedup_factor', 0):.2f}x")
        else:
            print(f"\n❌ Performance validation failed: {performance_results.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await validator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())