#!/usr/bin/env python3
"""
OW-KAI Technologies - Enterprise Documentation Generator
Creates comprehensive, visually stunning documentation with full technical depth
"""

import os
from datetime import datetime

def create_enhanced_documentation():
    """Generate comprehensive HTML documentation with all technical details"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OW-KAI Technologies - Enterprise Platform Documentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-bg: #1a202c;
            --card-bg: #ffffff;
            --text-primary: #2d3748;
            --text-secondary: #4a5568;
            --border-color: #e2e8f0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header Styles */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 60px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .header h1 {{
            font-size: 4em;
            margin-bottom: 15px;
            font-weight: 800;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
            letter-spacing: -1px;
        }}
        
        .header .subtitle {{
            font-size: 1.5em;
            margin-bottom: 20px;
            opacity: 0.95;
            font-weight: 300;
        }}
        
        .header .company-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
            padding-top: 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .info-item {{
            text-align: center;
        }}
        
        .info-label {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-size: 1.2em;
            font-weight: 600;
        }}
        
        /* Navigation Tabs */
        .nav-tabs {{
            display: flex;
            background: white;
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .nav-tab {{
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 15px;
            font-weight: 600;
            color: var(--text-secondary);
            transition: all 0.3s ease;
            border-radius: 10px;
            white-space: nowrap;
        }}
        
        .nav-tab:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: var(--primary-color);
        }}
        
        .nav-tab.active {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        
        /* Content Area */
        .content-area {{
            background: white;
            border-radius: 20px;
            padding: 50px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Typography */
        h2 {{
            color: var(--primary-color);
            font-size: 2.5em;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--primary-color);
            font-weight: 700;
        }}
        
        h3 {{
            color: var(--text-primary);
            font-size: 1.8em;
            margin: 40px 0 20px 0;
            font-weight: 600;
        }}
        
        h4 {{
            color: var(--primary-color);
            font-size: 1.3em;
            margin: 25px 0 15px 0;
            font-weight: 600;
        }}
        
        p {{
            margin-bottom: 15px;
            font-size: 1.05em;
            line-height: 1.8;
        }}
        
        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 35px 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            transition: all 0.5s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }}
        
        .stat-card:hover::before {{
            top: -10%;
            right: -10%;
        }}
        
        .stat-number {{
            font-size: 3.5em;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 1;
        }}
        
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.95;
            font-weight: 500;
            position: relative;
            z-index: 1;
        }}
        
        /* Feature Cards */
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        
        .feature-card {{
            background: linear-gradient(145deg, #f8fafc 0%, #ffffff 100%);
            border: 2px solid var(--border-color);
            padding: 30px;
            border-radius: 15px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .feature-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            transform: scaleY(0);
            transition: transform 0.3s ease;
        }}
        
        .feature-card:hover {{
            border-color: var(--primary-color);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.2);
            transform: translateY(-5px);
        }}
        
        .feature-card:hover::before {{
            transform: scaleY(1);
        }}
        
        .feature-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
        }}
        
        .feature-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 10px;
        }}
        
        .feature-description {{
            color: var(--text-secondary);
            line-height: 1.6;
        }}
        
        /* Alert Boxes */
        .alert {{
            padding: 20px 25px;
            margin: 25px 0;
            border-radius: 12px;
            border-left: 5px solid;
            display: flex;
            align-items: flex-start;
            gap: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .alert-icon {{
            font-size: 1.5em;
            flex-shrink: 0;
        }}
        
        .alert-success {{
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border-color: var(--success-color);
            color: #065f46;
        }}
        
        .alert-info {{
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            border-color: #3b82f6;
            color: #1e40af;
        }}
        
        .alert-warning {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-color: var(--warning-color);
            color: #92400e;
        }}
        
        /* Tables */
        .table-container {{
            overflow-x: auto;
            margin: 25px 0;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        
        th {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 18px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 1.05em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            font-size: 1em;
        }}
        
        tr:hover {{
            background: #f8fafc;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Code Blocks */
        code {{
            background: #2d3748;
            color: #68d391;
            padding: 3px 10px;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            font-weight: 500;
        }}
        
        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 25px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 25px 0;
            font-size: 0.95em;
            line-height: 1.6;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            position: relative;
        }}
        
        pre::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color), var(--accent-color));
        }}
        
        /* Lists */
        .feature-list {{
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }}
        
        .feature-list li {{
            padding: 18px 20px 18px 55px;
            margin: 12px 0;
            background: linear-gradient(145deg, #f8fafc 0%, #ffffff 100%);
            border-left: 4px solid var(--primary-color);
            border-radius: 8px;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .feature-list li::before {{
            content: "✓";
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            background: var(--primary-color);
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .feature-list li:hover {{
            background: linear-gradient(145deg, #edf2f7 0%, #f7fafc 100%);
            transform: translateX(10px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        /* Status Badges */
        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge-complete {{
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            color: #065f46;
        }}
        
        .badge-progress {{
            background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
            color: #7c2d12;
        }}
        
        .badge-planned {{
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1e3a8a;
        }}
        
        /* Architecture Diagram */
        .architecture-diagram {{
            background: linear-gradient(145deg, #f8fafc 0%, #ffffff 100%);
            padding: 40px;
            border-radius: 15px;
            margin: 30px 0;
            border: 2px solid var(--border-color);
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
            line-height: 1.8;
            overflow-x: auto;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        /* Timeline */
        .timeline {{
            position: relative;
            padding: 20px 0;
            margin: 30px 0;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 30px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(180deg, var(--primary-color), var(--secondary-color));
        }}
        
        .timeline-item {{
            position: relative;
            padding-left: 70px;
            margin-bottom: 30px;
        }}
        
        .timeline-marker {{
            position: absolute;
            left: 19px;
            top: 5px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--primary-color);
            border: 4px solid white;
            box-shadow: 0 0 0 4px var(--primary-color);
        }}
        
        .timeline-content {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid var(--border-color);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .timeline-date {{
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 10px;
        }}
        
        /* Pricing Cards */
        .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }}
        
        .pricing-card {{
            background: white;
            border: 3px solid var(--border-color);
            border-radius: 20px;
            padding: 40px 30px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .pricing-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .pricing-card:hover {{
            border-color: var(--primary-color);
            box-shadow: 0 20px 50px rgba(102, 126, 234, 0.3);
            transform: translateY(-10px);
        }}
        
        .pricing-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .pricing-card.featured {{
            border-color: var(--primary-color);
            box-shadow: 0 20px 50px rgba(102, 126, 234, 0.2);
        }}
        
        .pricing-card.featured::before {{
            transform: scaleX(1);
        }}
        
        .pricing-tier {{
            font-size: 1.5em;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 15px;
        }}
        
        .pricing-amount {{
            font-size: 3em;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 10px;
        }}
        
        .pricing-period {{
            color: var(--text-secondary);
            margin-bottom: 30px;
        }}
        
        .pricing-features {{
            list-style: none;
            padding: 0;
            margin: 30px 0;
            text-align: left;
        }}
        
        .pricing-features li {{
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .pricing-features li:last-child {{
            border-bottom: none;
        }}
        
        /* Footer */
        .footer {{
            background: #2d3748;
            color: white;
            padding: 50px 40px;
            border-radius: 20px;
            margin-top: 40px;
            box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .footer-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin-bottom: 30px;
        }}
        
        .footer-section h3 {{
            color: white;
            margin-bottom: 20px;
            font-size: 1.3em;
        }}
        
        .footer-section ul {{
            list-style: none;
            padding: 0;
        }}
        
        .footer-section li {{
            margin-bottom: 12px;
        }}
        
        .footer-section a {{
            color: #a0aec0;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .footer-section a:hover {{
            color: var(--accent-color);
        }}
        
        .footer-bottom {{
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #a0aec0;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2.5em;
            }}
            
            .header .subtitle {{
                font-size: 1.2em;
            }}
            
            .content-area {{
                padding: 30px 20px;
            }}
            
            h2 {{
                font-size: 2em;
            }}
            
            .stats-grid,
            .feature-grid,
            .pricing-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-content">
                <h1>🚀 OW-KAI Technologies</h1>
                <div class="subtitle">Enterprise AI Agent Governance Platform</div>
                <div class="company-info">
                    <div class="info-item">
                        <div class="info-label">Legal Entity</div>
                        <div class="info-value">Delaware C-Corporation</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Founded</div>
                        <div class="info-value">2025</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Status</div>
                        <div class="info-value">Production Ready</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Platform</div>
                        <div class="info-value">pilot.owkai.app</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('architecture')">🏗️ Architecture</button>
            <button class="nav-tab" onclick="showTab('features')">⚡ Features</button>
            <button class="nav-tab" onclick="showTab('database')">💾 Database</button>
            <button class="nav-tab" onclick="showTab('api')">🔌 API Routes</button>
            <button class="nav-tab" onclick="showTab('services')">⚙️ Services</button>
            <button class="nav-tab" onclick="showTab('deployment')">🚀 Deployment</button>
            <button class="nav-tab" onclick="showTab('security')">🔒 Security</button>
            <button class="nav-tab" onclick="showTab('business')">💼 Business</button>
            <button class="nav-tab" onclick="showTab('roadmap')">🗺️ Roadmap</button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <h2>Platform Overview</h2>
                
                <div class="alert alert-success">
                    <span class="alert-icon">✅</span>
                    <div>
                        <strong>Production Status:</strong> OW-KAI is 95% enterprise-ready and operational at 
                        <a href="https://pilot.owkai.app" target="_blank" style="color: #065f46; font-weight: 600;">https://pilot.owkai.app</a>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">135+</div>
                        <div class="stat-label">API Endpoints</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">18</div>
                        <div class="stat-label">Database Tables</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">29</div>
                        <div class="stat-label">Route Modules</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">24</div>
                        <div class="stat-label">Backend Services</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">95%</div>
                        <div class="stat-label">Enterprise Ready</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">99.9%</div>
                        <div class="stat-label">Target Uptime</div>
                    </div>
                </div>

                <h3>Executive Summary</h3>
                <p>
                    OW-KAI is an <strong>Enterprise AI Agent Governance Platform</strong> that provides real-time monitoring, 
                    risk assessment, and human-in-the-loop (HITL) approval workflows for AI agents and Model Context Protocol 
                    (MCP) servers in enterprise environments. The platform addresses the critical need for secure, compliant 
                    AI governance by providing comprehensive oversight, security insights, and control mechanisms for AI agent deployments.
                </p>

                <h3>Core Value Proposition</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">Real-time Risk Assessment</div>
                        <div class="feature-description">
                            30-100 point scoring system that evaluates AI agent actions before execution with <200ms average response time
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">👥</div>
                        <div class="feature-title">Human-in-the-Loop Workflows</div>
                        <div class="feature-description">
                            Multi-level approval chains for medium and high-risk actions with automated routing based on risk scores
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📝</div>
                        <div class="feature-title">Complete Audit Trails</div>
                        <div class="feature-description">
                            Immutable compliance logging for SOC2, GDPR, and enterprise requirements with full user attribution
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔌</div>
                        <div class="feature-title">MCP Governance</div>
                        <div class="feature-description">
                            Native integration with Model Context Protocol for standardized AI agent control across platforms
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🤖</div>
                        <div class="feature-title">Smart Rules Engine</div>
                        <div class="feature-description">
                            AI-powered policy creation with natural language processing using GPT-4 for intelligent automation
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🚨</div>
                        <div class="feature-title">Smart Alert Management</div>
                        <div class="feature-description">
                            Real-time threat detection with background monitoring every 30 seconds and WebSocket streaming
                        </div>
                    </div>
                </div>

                <h3>Company Information</h3>
                <div class="alert alert-info">
                    <span class="alert-icon">🏢</span>
                    <div>
                        <strong>OW-KAI Technologies, Inc.</strong><br>
                        Delaware C-Corporation | Founded 2025<br>
                        Founder & CEO: Donald King (Veteran Entrepreneur)<br>
                        Status: Pre-seed stage, seeking Techstars acceptance
                    </div>
                </div>

                <h3>Problem Statement</h3>
                <p>
                    Enterprises deploying AI agents face critical security and compliance challenges:
                </p>
                <ul class="feature-list">
                    <li>AI agents operate autonomously without proper oversight</li>
                    <li>High-risk actions (data deletion, API calls, system modifications) execute without approval</li>
                    <li>No standardized governance framework for AI agent activities</li>
                    <li>Compliance requirements (SOC2, GDPR, HIPAA) demand comprehensive audit trails</li>
                    <li>Security teams lack real-time visibility into AI agent operations</li>
                </ul>

                <h3>Solution</h3>
                <p>
                    OW-KAI acts as a <strong>unified AI governance layer</strong> that sits between AI agents/MCP servers 
                    and enterprise systems, providing:
                </p>
                <ul class="feature-list">
                    <li><strong>Detection & Interception:</strong> All AI agent actions flow through OW-KAI gateway for analysis</li>
                    <li><strong>Risk Assessment:</strong> Real-time evaluation using configurable 30-100 point risk matrices</li>
                    <li><strong>Approval Workflows:</strong> Automated routing based on risk scores with multi-level chains</li>
                    <li><strong>Execution Control:</strong> Block, approve, or conditionally allow actions with justification</li>
                    <li><strong>Audit & Compliance:</strong> Complete immutable logging with user attribution and timestamps</li>
                </ul>
            </div>

            <!-- Architecture Tab -->
            <div id="architecture" class="tab-content">
                <h2>Technical Architecture</h2>

                <h3>High-Level System Architecture</h3>
                <div class="architecture-diagram">
┌────────────────────────────────────────────────────────────────┐
│                     OW-KAI Platform                            │
├────────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  API Gateway     │  Admin Portal       │
│  - Dashboard          │  - Load Balancer │  - User Management  │
│  - Auth Center        │  - Rate Limiting │  - Policy Config    │
│  - Alert Management   │  - SSL/TLS       │  - Audit Viewer     │
├────────────────────────────────────────────────────────────────┤
│              Backend Services (FastAPI)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Auth      │ │ MCP Gateway │ │ Risk Engine │              │
│  │  RS256 JWT  │ │ Protocol    │ │ 30-100 Score│              │
│  │  RBAC/ABAC  │ │ Proxy       │ │ ML Model    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │Smart Rules  │ │ Analytics   │ │Alert System │              │
│  │ AI Engine   │ │ Metrics API │ │ Real-time   │              │
│  │ OpenAI GPT-4│ │ Dashboards  │ │ WebSocket   │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├────────────────────────────────────────────────────────────────┤
│                   Data Layer                                   │
│  ┌─────────────────────────────────────────────────┐           │
│  │  PostgreSQL 15 (AWS RDS Multi-AZ)               │           │
│  │  - Agent Actions & Workflows                    │           │
│  │  - Smart Rules & Policies                       │           │
│  │  - Approval Chains & History                    │           │
│  │  - Audit Trails & Compliance Logs               │           │
│  │  - User Management & RBAC                       │           │
│  └─────────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────────┘
                </div>

                <h3>Technology Stack</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">⚛️</div>
                        <div class="feature-title">Frontend Stack</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• React 18.2.0</li>
                                <li>• Vite 4.4.5</li>
                                <li>• Tailwind CSS 3.3.3</li>
                                <li>• shadcn/ui components</li>
                                <li>• WebSocket for real-time</li>
                                <li>• Lucide React icons</li>
                                <li>• Recharts visualization</li>
                            </ul>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🐍</div>
                        <div class="feature-title">Backend Stack</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• Python 3.11</li>
                                <li>• FastAPI 0.104.1</li>
                                <li>• SQLAlchemy 2.0.23</li>
                                <li>• Alembic migrations</li>
                                <li>• Uvicorn ASGI server</li>
                                <li>• Pydantic 2.5.0</li>
                                <li>• OpenAI 1.3.0 (GPT-4)</li>
                            </ul>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">☁️</div>
                        <div class="feature-title">Infrastructure</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• AWS ECS Fargate</li>
                                <li>• PostgreSQL 15 (RDS)</li>
                                <li>• Application Load Balancer</li>
                                <li>• CloudWatch monitoring</li>
                                <li>• ECR container registry</li>
                                <li>• Secrets Manager</li>
                                <li>• VPC networking</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h3>Authentication System</h3>
                <div class="alert alert-info">
                    <span class="alert-icon">🔐</span>
                    <div>
                        <strong>Cookie-Based RS256 JWT Authentication</strong><br><br>
                        <strong>Primary Method:</strong> Secure HTTP-only cookies with RS256 JWT tokens<br>
                        <strong>Key Storage:</strong> AWS Secrets Manager with automatic rotation<br>
                        <strong>Token Expiration:</strong> 8 hours (configurable)<br>
                        <strong>Also Supports:</strong> Bearer token authentication (Authorization header)<br>
                        <strong>Security:</strong> Bcrypt password hashing, XSS protection, CSRF protection
                    </div>
                </div>

                <h3>Workflow Architecture</h3>
                <div class="architecture-diagram">
┌─────────────┐
│  AI Agent   │
│  or MCP     │
│  Client     │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  OW-KAI Gateway      │
│  - Action Detection  │
│  - Risk Assessment   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐      ┌─────────────────┐
│  Risk Score: 0-100   │──────│ Auto-Approve    │
│                      │      │ (Score < 50)    │
│  • Low: 0-49        │      └─────────────────┘
│  • Medium: 50-69    │      ┌─────────────────┐
│  • High: 70-89      │──────│ Manager Approval│
│  • Critical: 90-100 │      │ (Score 50-69)   │
└──────┬───────────────┘      └─────────────────┘
       │                      ┌─────────────────┐
       │                      │ Multi-Level     │
       └──────────────────────│ Approval Chain  │
                              │ (Score 70+)     │
                              └─────────────────┘
                                     │
                                     ▼
                              ┌─────────────────┐
                              │ Execute Action  │
                              │ + Audit Log     │
                              └─────────────────┘
                </div>

                <h3>Deployment Configuration</h3>
                <pre>
<strong>Backend ECS Service:</strong>
  Service Name: owkai-pilot-backend-service
  Task Definition: owkai-pilot-backend:latest
  Desired Count: 2 (auto-scaling enabled)
  CPU: 256 units (.25 vCPU per task)
  Memory: 512 MB per task
  Container Port: 8000
  Health Check: /health endpoint every 30s

<strong>Frontend ECS Service:</strong>
  Service Name: owkai-pilot-frontend-service
  Task Definition: owkai-pilot-frontend:latest
  Desired Count: 2
  CPU: 256 units
  Memory: 512 MB
  Container Port: 80
  Health Check: / endpoint every 30s

<strong>RDS Database:</strong>
  Instance Class: db.t3.medium
  Engine: PostgreSQL 15.4
  Storage: 100 GB SSD (gp3)
  Multi-AZ: Enabled
  Encryption: At-rest and in-transit
  Backup Retention: 7 days
  Deletion Protection: Enabled
                </pre>
            </div>

            <!-- Features Tab -->
            <div id="features" class="tab-content">
                <h2>Core Features & Capabilities</h2>

                <h3>1. Authorization Center</h3>
                <div class="feature-card">
                    <div class="feature-title">Central Hub for AI Action Approval</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Central hub for reviewing and approving AI agent actions that require human oversight.</p>
                        
                        <h4>Key Features:</h4>
                        <ul class="feature-list">
                            <li><strong>Pending Actions Dashboard:</strong> Real-time view of all actions awaiting approval with filtering and sorting</li>
                            <li><strong>Multi-Tab Interface:</strong> Organized by Pending, Workflows, Performance Metrics, Automation, Execution History</li>
                            <li><strong>Action Details:</strong> Complete context including agent ID, action type, resource, risk score, timestamp</li>
                            <li><strong>Approve/Reject Controls:</strong> One-click approval or rejection with justification notes and audit trail</li>
                            <li><strong>Emergency Override:</strong> Break-glass functionality for critical situations requiring immediate action</li>
                            <li><strong>Audit Trail Integration:</strong> Every decision logged with user attribution, timestamps, and reasoning</li>
                        </ul>

                        <h4>Risk-Based Routing:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• <strong>Low Risk (0-49):</strong> Auto-approved with audit logging only</li>
                            <li>• <strong>Medium Risk (50-69):</strong> Single-level manager approval required</li>
                            <li>• <strong>High Risk (70-89):</strong> Two-level approval (Department Head + Security Officer)</li>
                            <li>• <strong>Critical Risk (90-100):</strong> Three-level approval with compliance review</li>
                        </ul>
                    </div>
                </div>

                <h3>2. Risk Assessment Engine</h3>
                <div class="feature-card">
                    <div class="feature-title">Intelligent 30-100 Point Risk Scoring</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Real-time evaluation of AI agent actions using a sophisticated 30-100 point scoring algorithm.</p>
                        
                        <h4>Risk Factors Evaluated:</h4>
                        <ol style="margin-left: 20px; margin-top: 10px;">
                            <li><strong>Action Type:</strong> delete=100, write=70, read=30, list=10</li>
                            <li><strong>Resource Sensitivity:</strong> database=+30, API=+20, files=+15</li>
                            <li><strong>Temporal Context:</strong> After-hours execution (+10 points)</li>
                            <li><strong>Compliance Impact:</strong> GDPR/HIPAA data access (+15 points)</li>
                            <li><strong>Historical Patterns:</strong> Anomaly detection based on agent behavior</li>
                        </ol>

                        <h4>Performance:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• Average response time: <strong><200ms</strong></li>
                            <li>• Real-time processing with ML model integration</li>
                            <li>• Configurable risk thresholds per organization</li>
                            <li>• Pattern recognition for anomaly detection</li>
                        </ul>
                    </div>
                </div>

                <h3>3. Smart Rules Engine</h3>
                <div class="feature-card">
                    <div class="feature-title">AI-Powered Policy Creation</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> AI-powered policy creation and enforcement using natural language processing with GPT-4.</p>
                        
                        <h4>Key Capabilities:</h4>
                        <ul class="feature-list">
                            <li><strong>Natural Language Rule Creation:</strong> "Block file access exceeding 100 files per minute"</li>
                            <li><strong>OpenAI GPT-4 Integration:</strong> Intelligent rule generation and validation</li>
                            <li><strong>A/B Testing Framework:</strong> Evaluate rule effectiveness before full deployment</li>
                            <li><strong>Performance Analytics:</strong> Track rule triggers, false positives, effectiveness scores</li>
                            <li><strong>Version Control:</strong> Complete rule history and rollback capabilities</li>
                            <li><strong>Compliance Mappings:</strong> Automatic mapping to SOC2, GDPR, HIPAA frameworks</li>
                        </ul>

                        <h4>Example Rule Structure:</h4>
                        <pre style="margin-top: 15px;">{{
  "name": "Block High-Volume File Access",
  "condition": "smart_analysis(action, 'file_access_count') > 100",
  "action": "block",
  "risk_level": "high",
  "compliance_impact": "Data loss prevention (SOC2 CC6.1)",
  "false_positive_likelihood": "low",
  "performance_score": 85
}}</pre>
                    </div>
                </div>

                <h3>4. Smart Alert Management System</h3>
                <div class="feature-card">
                    <div class="feature-title">Real-Time Threat Detection</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Real-time alert monitoring with background evaluation of smart rules every 30 seconds.</p>
                        
                        <h4>5-Tab Alert Interface:</h4>
                        <ol style="margin-left: 20px; margin-top: 10px;">
                            <li><strong>Active Alerts:</strong> Current threats requiring immediate attention</li>
                            <li><strong>Alert History:</strong> Historical log of all alerts with resolution status</li>
                            <li><strong>Rule Triggers:</strong> Which rules generated alerts with context</li>
                            <li><strong>Performance Metrics:</strong> Alert accuracy and response times</li>
                            <li><strong>Configuration:</strong> Alert thresholds and notification settings</li>
                        </ol>

                        <h4>Background Monitoring:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• Async task execution every 30 seconds</li>
                            <li>• Evaluates active smart rules against system metrics</li>
                            <li>• Triggers alerts when threat conditions detected</li>
                            <li>• WebSocket streaming for real-time updates</li>
                        </ul>

                        <h4>Alert Types:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• 🚨 Security threats (unauthorized access attempts)</li>
                            <li>• ⚠️ Compliance violations (policy breaches)</li>
                            <li>• 📊 Performance anomalies (unusual patterns)</li>
                            <li>• 🔧 System health issues (service degradation)</li>
                        </ul>
                    </div>
                </div>

                <h3>5. MCP (Model Context Protocol) Governance</h3>
                <div class="feature-card">
                    <div class="feature-title">Standards-Based AI Agent Control</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Native integration with MCP for standardized AI agent control across platforms.</p>
                        
                        <h4>Key Features:</h4>
                        <ul class="feature-list">
                            <li><strong>MCP Action Ingestion:</strong> <code>/mcp/actions/ingest</code> endpoint for seamless integration</li>
                            <li><strong>Protocol Proxy:</strong> OW-KAI acts as MCP gateway for all agent communications</li>
                            <li><strong>Action Audit:</strong> Complete logging of MCP communications with context</li>
                            <li><strong>Approval Integration:</strong> MCP actions route through same workflow system</li>
                            <li><strong>Statistics API:</strong> Real-time MCP action metrics and compliance reporting</li>
                        </ul>

                        <h4>MCP Integration Flow:</h4>
                        <pre style="margin-top: 15px;">MCP Client → OW-KAI MCP Proxy → Risk Assessment → 
Approval Workflow → Target MCP Server → Response → Audit Log</pre>
                    </div>
                </div>

                <h3>6. Enterprise Dashboard</h3>
                <div class="feature-card">
                    <div class="feature-title">Executive Visibility & Analytics</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Executive and operational visibility into AI governance metrics.</p>
                        
                        <h4>Dashboard Sections:</h4>
                        <ul class="feature-list">
                            <li><strong>Overview Cards:</strong> Total actions, pending approvals, average risk score, compliance status</li>
                            <li><strong>Real-Time Activity Feed:</strong> Live stream of agent actions color-coded by risk level</li>
                            <li><strong>Performance Metrics:</strong> Approval workflow efficiency, response times, false positive rates</li>
                            <li><strong>Analytics Charts:</strong> Actions by risk level, trends over time, top agents, compliance metrics</li>
                        </ul>
                    </div>
                </div>

                <h3>7. User Management & RBAC</h3>
                <div class="feature-card">
                    <div class="feature-title">Enterprise Authentication & Authorization</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Enterprise-grade user authentication and role-based access control.</p>
                        
                        <h4>User Roles:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• <strong>Admin:</strong> Full system access, user management, configuration</li>
                            <li>• <strong>Manager:</strong> Approve medium/high-risk actions, view dashboards</li>
                            <li>• <strong>Analyst:</strong> View-only access to dashboards and reports</li>
                            <li>• <strong>User:</strong> Limited access to own actions and basic features</li>
                        </ul>

                        <h4>Security Features:</h4>
                        <ul class="feature-list" style="margin-top: 15px;">
                            <li>RS256 JWT authentication with rotating keys from AWS Secrets Manager</li>
                            <li>Secure HTTP-only cookies for token storage (XSS protection)</li>
                            <li>Password hashing with bcrypt and configurable salt rounds</li>
                            <li>Session management with configurable timeouts</li>
                            <li>Multi-factor authentication (planned)</li>
                            <li>SSO integration support (Okta, Azure AD - planned)</li>
                        </ul>
                    </div>
                </div>

                <h3>8. Audit Trail & Compliance</h3>
                <div class="feature-card">
                    <div class="feature-title">Immutable Compliance Logging</div>
                    <div class="feature-description">
                        <p><strong>Purpose:</strong> Immutable audit logs for regulatory compliance and forensic analysis.</p>
                        
                        <h4>Audit Log Captures:</h4>
                        <ul class="feature-list">
                            <li>All AI agent actions (approved, rejected, auto-approved)</li>
                            <li>User decisions with justifications and reasoning</li>
                            <li>Risk assessment calculations and contributing factors</li>
                            <li>System configuration changes with before/after states</li>
                            <li>User authentication events and session management</li>
                            <li>Policy modifications with version control</li>
                        </ul>

                        <h4>Compliance Frameworks Supported:</h4>
                        <ul style="list-style: none; padding: 0; margin-top: 15px;">
                            <li>• <strong>SOC2:</strong> Access controls, audit trails, incident response</li>
                            <li>• <strong>GDPR:</strong> Data processing logs, consent tracking, deletion records</li>
                            <li>• <strong>HIPAA:</strong> PHI access logs, user attribution (healthcare customers)</li>
                            <li>• <strong>ISO 27001:</strong> Information security management standards</li>
                        </ul>

                        <h4>Audit Features:</h4>
                        <ul class="feature-list" style="margin-top: 15px;">
                            <li>Immutable log storage with tamper-evident logging</li>
                            <li>Timestamp with timezone support for global deployments</li>
                            <li>User attribution for all actions</li>
                            <li>Export to CSV/JSON for external audits</li>
                            <li>Long-term retention policies (configurable)</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Database Tab -->
            <div id="database" class="tab-content">
                <h2>Database Architecture</h2>

                <div class="alert alert-info">
                    <span class="alert-icon">💾</span>
                    <div>
                        <strong>Database Engine:</strong> PostgreSQL 15.4 on AWS RDS<br>
                        <strong>Configuration:</strong> Multi-AZ deployment with automatic failover<br>
                        <strong>Instance:</strong> db.t3.medium<br>
                        <strong>Storage:</strong> 100 GB SSD (gp3) with automatic scaling
                    </div>
                </div>

                <h3>Core Tables (18 Total)</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Table Name</th>
                                <th>Purpose</th>
                                <th>Key Fields</th>
                                <th>Relationships</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>users</code></td>
                                <td>User accounts and roles</td>
                                <td>email, hashed_password, role, is_active</td>
                                <td>→ agent_actions, audit_logs</td>
                            </tr>
                            <tr>
                                <td><code>agent_actions</code></td>
                                <td>All AI agent actions</td>
                                <td>agent_id, action_type, resource, risk_score, status</td>
                                <td>← users, → workflows</td>
                            </tr>
                            <tr>
                                <td><code>pending_agent_actions</code></td>
                                <td>Actions awaiting approval</td>
                                <td>action_id, status, priority, created_at</td>
                                <td>← agent_actions</td>
                            </tr>
                            <tr>
                                <td><code>workflows</code></td>
                                <td>Multi-stage approval workflows</td>
                                <td>action_id, status, current_stage, max_stages</td>
                                <td>← agent_actions, → workflow_steps</td>
                            </tr>
                            <tr>
                                <td><code>workflow_executions</code></td>
                                <td>Workflow execution tracking</td>
                                <td>workflow_id, status, started_at, completed_at</td>
                                <td>← workflows</td>
                            </tr>
                            <tr>
                                <td><code>workflow_steps</code></td>
                                <td>Individual approval stages</td>
                                <td>workflow_id, step_number, approver_id, status</td>
                                <td>← workflows, ← users</td>
                            </tr>
                            <tr>
                                <td><code>smart_rules</code></td>
                                <td>AI-powered policy rules</td>
                                <td>name, condition, action, risk_level, performance_score</td>
                                <td>→ rule_feedbacks</td>
                            </tr>
                            <tr>
                                <td><code>rules</code></td>
                                <td>Traditional policy rules</td>
                                <td>name, condition, action, is_active</td>
                                <td>None</td>
                            </tr>
                            <tr>
                                <td><code>rule_feedbacks</code></td>
                                <td>Rule performance tracking</td>
                                <td>rule_id, accuracy, false_positive_rate, trigger_count</td>
                                <td>← smart_rules</td>
                            </tr>
                            <tr>
                                <td><code>enterprise_policies</code></td>
                                <td>Organization-wide policies</td>
                                <td>name, description, policy_type, enforcement_level</td>
                                <td>None</td>
                            </tr>
                            <tr>
                                <td><code>alerts</code></td>
                                <td>Real-time security alerts</td>
                                <td>alert_type, severity, status, description</td>
                                <td>None</td>
                            </tr>
                            <tr>
                                <td><code>logs</code></td>
                                <td>System activity logs</td>
                                <td>level, message, source, timestamp</td>
                                <td>→ log_audit_trails</td>
                            </tr>
                            <tr>
                                <td><code>log_audit_trails</code></td>
                                <td>Immutable log records</td>
                                <td>log_id, hash, signature, created_at</td>
                                <td>← logs</td>
                            </tr>
                            <tr>
                                <td><code>audit_logs</code></td>
                                <td>Compliance audit trail</td>
                                <td>user_id, action, resource_type, details, ip_address</td>
                                <td>← users</td>
                            </tr>
                            <tr>
                                <td><code>automation_playbooks</code></td>
                                <td>Automation workflows</td>
                                <td>name, triggers, actions, schedule</td>
                                <td>→ playbook_executions</td>
                            </tr>
                            <tr>
                                <td><code>playbook_executions</code></td>
                                <td>Playbook execution history</td>
                                <td>playbook_id, status, result, execution_time</td>
                                <td>← automation_playbooks</td>
                            </tr>
                            <tr>
                                <td><code>system_configurations</code></td>
                                <td>System-wide settings</td>
                                <td>key, value, data_type, updated_at</td>
                                <td>None</td>
                            </tr>
                            <tr>
                                <td><code>integration_endpoints</code></td>
                                <td>External integrations</td>
                                <td>name, url, auth_type, api_key, is_active</td>
                                <td>None</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>Database Schema Diagram</h3>
                <div class="architecture-diagram">
┌─────────────────┐
│     users       │
│  - id (PK)      │
│  - email        │
│  - password     │
│  - role         │
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌──────────────────┐  ┌────────────────┐
│  agent_actions   │  │  audit_logs    │
│  - id (PK)       │  │  - id (PK)     │
│  - agent_id      │  │  - user_id (FK)│
│  - action_type   │  │  - action      │
│  - risk_score    │  │  - details     │
│  - user_id (FK)  │  └────────────────┘
└────────┬─────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌──────────────────┐  ┌─────────────────────┐
│   workflows      │  │ pending_agent_      │
│  - id (PK)       │  │ actions             │
│  - action_id (FK)│  │  - id (PK)          │
│  - status        │  │  - action_id (FK)   │
│  - current_stage │  └─────────────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  workflow_steps  │
│  - id (PK)       │
│  - workflow_id   │
│  - approver_id   │
└──────────────────┘

┌─────────────────┐
│  smart_rules    │
│  - id (PK)      │
│  - name         │
│  - condition    │
│  - action       │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ rule_feedbacks   │
│  - id (PK)       │
│  - rule_id (FK)  │
│  - accuracy      │
└──────────────────┘

┌──────────────────┐
│  alerts          │
│  - id (PK)       │
│  - alert_type    │
│  - severity      │
│  - status        │
└──────────────────┘

┌──────────────────┐
│  logs            │
│  - id (PK)       │
│  - level         │
│  - message       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ log_audit_trails │
│  - id (PK)       │
│  - log_id (FK)   │
│  - hash          │
└──────────────────┘
                </div>

                <h3>Database Configuration</h3>
                <pre>
<strong>Instance Configuration:</strong>
  Instance Class: db.t3.medium (2 vCPUs, 4 GB RAM)
  Storage: 100 GB SSD (gp3)
  IOPS: 3000 (baseline)
  Multi-AZ: Enabled (automatic failover)
  
<strong>Security:</strong>
  Encryption at Rest: AES-256
  Encryption in Transit: SSL/TLS required
  Access: VPC private subnet only
  Security Groups: Restrict to ECS tasks only
  
<strong>Backup & Recovery:</strong>
  Automated Backups: Enabled
  Backup Window: 02:00-03:00 UTC
  Retention Period: 7 days
  Maintenance Window: Sun:03:00-04:00 UTC
  Point-in-Time Recovery: Enabled
  
<strong>Performance:</strong>
  Connection Pool: 20 connections
  Max Connections: 100
  Query Timeout: 30 seconds
  Average Query Time: <50ms
                </pre>

                <h3>Database Migrations</h3>
                <div class="alert alert-info">
                    <span class="alert-icon">🔄</span>
                    <div>
                        <strong>Migration Tool:</strong> Alembic<br>
                        <strong>Migration Location:</strong> <code>backend/alembic/versions/</code><br>
                        <strong>Run Migrations:</strong> <code>alembic upgrade head</code><br>
                        <strong>Create Migration:</strong> <code>alembic revision --autogenerate -m "description"</code>
                    </div>
                </div>
            </div>

            <!-- API Routes Tab -->
            <div id="api" class="tab-content">
                <h2>API Routes & Endpoints</h2>

                <div class="alert alert-success">
                    <span class="alert-icon">🔌</span>
                    <div>
                        <strong>Base URL:</strong> https://pilot.owkai.app<br>
                        <strong>API Documentation:</strong> <a href="https://pilot.owkai.app/docs" target="_blank" style="color: #065f46; font-weight: 600;">https://pilot.owkai.app/docs</a> (OpenAPI/Swagger)<br>
                        <strong>Total Endpoints:</strong> 135+ enterprise-grade APIs
                    </div>
                </div>

                <h3>Route Modules (29 Total)</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Endpoints</th>
                                <th>Purpose</th>
                                <th>Key Routes</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>admin_routes</code></td>
                                <td>3</td>
                                <td>Administrative functions</td>
                                <td>/admin/config, /admin/system</td>
                            </tr>
                            <tr>
                                <td><code>agent_routes</code></td>
                                <td>7</td>
                                <td>Agent management</td>
                                <td>/agents, /agents/{{id}}, /agents/stats</td>
                            </tr>
                            <tr>
                                <td><code>alert_routes</code></td>
                                <td>4</td>
                                <td>Alert management</td>
                                <td>/alerts/active, /alerts/history</td>
                            </tr>
                            <tr>
                                <td><code>alert_summary</code></td>
                                <td>2</td>
                                <td>Alert summaries</td>
                                <td>/alerts/summary, /alerts/metrics</td>
                            </tr>
                            <tr>
                                <td><code>analytics_routes</code></td>
                                <td>8</td>
                                <td>Analytics & metrics</td>
                                <td>/analytics/dashboard, /analytics/trends</td>
                            </tr>
                            <tr>
                                <td><code>audit_routes</code></td>
                                <td>4</td>
                                <td>Audit logging</td>
                                <td>/audit/logs, /audit/export</td>
                            </tr>
                            <tr>
                                <td><code>auth_routes</code></td>
                                <td>7</td>
                                <td>Authentication</td>
                                <td>/auth/token, /auth/me, /auth/logout</td>
                            </tr>
                            <tr>
                                <td><code>authorization_api_adapter</code></td>
                                <td>6</td>
                                <td>Authorization workflows</td>
                                <td>/api/authorization/dashboard</td>
                            </tr>
                            <tr>
                                <td><code>authorization_routes</code></td>
                                <td>12</td>
                                <td>Approval management</td>
                                <td>/authorization/approve, /authorization/reject</td>
                            </tr>
                            <tr>
                                <td><code>automation_orchestration_routes</code></td>
                                <td>7</td>
                                <td>Automation workflows</td>
                                <td>/automation/playbooks, /automation/execute</td>
                            </tr>
                            <tr>
                                <td><code>data_rights_routes</code></td>
                                <td>12</td>
                                <td>Data privacy compliance</td>
                                <td>/data-rights/request, /data-rights/export</td>
                            </tr>
                            <tr>
                                <td><code>enterprise_secrets_routes</code></td>
                                <td>12</td>
                                <td>Secret management</td>
                                <td>/secrets, /secrets/rotate</td>
                            </tr>
                            <tr>
                                <td><code>enterprise_user_management_routes</code></td>
                                <td>12</td>
                                <td>User administration</td>
                                <td>/api/users, /api/users/{{id}}, /api/users/stats</td>
                            </tr>
                            <tr>
                                <td><code>log_routes</code></td>
                                <td>2</td>
                                <td>System logging</td>
                                <td>/logs, /logs/search</td>
                            </tr>
                            <tr>
                                <td><code>main_routes</code></td>
                                <td>3</td>
                                <td>Core platform routes</td>
                                <td>/health, /, /status</td>
                            </tr>
                            <tr>
                                <td><code>mcp_enterprise_secure</code></td>
                                <td>3</td>
                                <td>Secure MCP operations</td>
                                <td>/mcp/secure/action, /mcp/secure/validate</td>
                            </tr>
                            <tr>
                                <td><code>mcp_governance_adapter</code></td>
                                <td>2</td>
                                <td>MCP governance bridge</td>
                                <td>/mcp/adapter/route, /mcp/adapter/stats</td>
                            </tr>
                            <tr>
                                <td><code>mcp_governance_routes</code></td>
                                <td>13</td>
                                <td>MCP management</td>
                                <td>/mcp/actions/ingest, /mcp/approve/{{id}}</td>
                            </tr>
                            <tr>
                                <td><code>rule_routes</code></td>
                                <td>7</td>
                                <td>Rule management</td>
                                <td>/rules, /rules/{{id}}, /rules/test</td>
                            </tr>
                            <tr>
                                <td><code>siem_integration</code></td>
                                <td>10</td>
                                <td>SIEM integration</td>
                                <td>/siem/events, /siem/export</td>
                            </tr>
                            <tr>
                                <td><code>siem_simple</code></td>
                                <td>6</td>
                                <td>Simple SIEM functions</td>
                                <td>/siem/simple/query, /siem/simple/alert</td>
                            </tr>
                            <tr>
                                <td><code>smart_alerts</code></td>
                                <td>5</td>
                                <td>Smart alerting system</td>
                                <td>/smart-alerts/active, /smart-alerts/config</td>
                            </tr>
                            <tr>
                                <td><code>smart_rules_routes</code></td>
                                <td>15</td>
                                <td>Smart rules engine</td>
                                <td>/api/smart-rules, /api/smart-rules/generate-from-nl</td>
                            </tr>
                            <tr>
                                <td><code>sso_routes</code></td>
                                <td>5</td>
                                <td>Single Sign-On</td>
                                <td>/sso/login, /sso/callback, /sso/metadata</td>
                            </tr>
                            <tr>
                                <td><code>support_routes</code></td>
                                <td>1</td>
                                <td>Support system</td>
                                <td>/support/ticket</td>
                            </tr>
                            <tr>
                                <td><code>unified_governance_routes</code></td>
                                <td>27</td>
                                <td>Unified governance platform</td>
                                <td>/governance/policies, /governance/compliance</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>Key API Endpoint Examples</h3>
                
                <h4>Authentication Endpoints</h4>
                <pre>
<strong>POST /auth/token</strong>
Description: Login and obtain JWT token
Request Body: {{ "username": "user@example.com", "password": "..." }}
Response: {{ "access_token": "...", "token_type": "bearer" }}

<strong>GET /auth/me</strong>
Description: Get current authenticated user information
Headers: Authorization: Bearer {{token}}
Response: {{ "id": 1, "email": "...", "role": "admin" }}

<strong>POST /auth/logout</strong>
Description: Logout and invalidate token
Headers: Authorization: Bearer {{token}}
Response: {{ "message": "Successfully logged out" }}
                </pre>

                <h4>Agent Action Endpoints</h4>
                <pre>
<strong>POST /agent-actions</strong>
Description: Submit new AI agent action for evaluation
Request Body: {{
  "agent_id": "agent-123",
  "action_type": "read",
  "resource": "database",
  "description": "Query user table"
}}
Response: {{
  "id": 1,
  "risk_score": 35,
  "status": "auto_approved",
  "audit_log_id": 456
}}

<strong>GET /agent-actions</strong>
Description: List all agent actions with filtering
Query Params: ?status=pending&risk_level=high&limit=50
Response: {{ "actions": [...], "total": 150, "page": 1 }}

<strong>GET /agent-actions/stats</strong>
Description: Get agent action statistics
Response: {{
  "total_actions": 1000,
  "auto_approved": 850,
  "pending": 50,
  "rejected": 100,
  "average_risk_score": 42
}}
                </pre>

                <h4>MCP Governance Endpoints</h4>
                <pre>
<strong>POST /mcp/actions/ingest</strong>
Description: Ingest MCP action for governance
Request Body: {{
  "action": "write",
  "resource": "file_system",
  "agent_id": "mcp-agent-1",
  "context": {{ ... }}
}}
Response: {{
  "action_id": 789,
  "risk_score": 68,
  "requires_approval": true,
  "workflow_id": 12
}}

<strong>GET /mcp/actions/stats</strong>
Description: Get MCP action statistics
Response: {{
  "total_mcp_actions": 500,
  "approved": 425,
  "rejected": 25,
  "pending": 50
}}
                </pre>

                <h4>Smart Rules Endpoints</h4>
                <pre>
<strong>POST /api/smart-rules/generate-from-nl</strong>
Description: Generate rule from natural language using GPT-4
Request Body: {{
  "description": "Block file access exceeding 100 files per minute"
}}
Response: {{
  "rule": {{
    "name": "High Volume File Access Block",
    "condition": "file_access_rate > 100/minute",
    "action": "block",
    "risk_level": "high",
    "confidence": 0.95
  }}
}}

<strong>GET /api/smart-rules/performance</strong>
Description: Get rule performance metrics
Response: {{
  "rules": [
    {{
      "id": 1,
      "name": "...",
      "trigger_count": 150,
      "false_positive_rate": 0.06,
      "effectiveness_score": 85
    }}
  ]
}}
                </pre>

                <h4>Authorization Center Endpoints</h4>
                <pre>
<strong>GET /api/authorization/dashboard</strong>
Description: Get authorization dashboard metrics
Response: {{
  "pending_actions": 15,
  "pending_workflows": 8,
  "average_approval_time": "5.2 minutes",
  "approval_rate": 0.92
}}

<strong>POST /api/authorization/approve/{{id}}</strong>
Description: Approve a pending action
Request Body: {{ "justification": "Approved after review" }}
Response: {{
  "status": "approved",
  "action_id": 123,
  "approved_by": "user@example.com",
  "timestamp": "2025-10-23T12:34:56Z"
}}
                </pre>
            </div>

            <!-- Services Tab -->
            <div id="services" class="tab-content">
                <h2>Backend Services</h2>

                <p>
                    OW-KAI's backend architecture consists of <strong>24 specialized microservices</strong> that work together 
                    to provide comprehensive AI agent governance. Each service is designed with a single responsibility principle 
                    and communicates through well-defined interfaces.
                </p>

                <h3>Service Categories</h3>

                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <div class="feature-title">Action Processing Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>action_service:</strong> Core agent action processing and validation</li>
                                <li>• <strong>action_taxonomy:</strong> Action classification and categorization</li>
                                <li>• <strong>pending_actions_service:</strong> Queue management for pending actions</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">Risk Assessment Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>assessment_service:</strong> Main risk scoring engine (30-100 points)</li>
                                <li>• <strong>cvss_calculator:</strong> CVSS-based risk calculation for vulnerabilities</li>
                                <li>• <strong>cvss_auto_mapper:</strong> Automatic CVSS mapping for threats</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">📋</div>
                        <div class="feature-title">Policy & Rules Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>cedar_enforcement_service:</strong> Policy enforcement using Cedar language</li>
                                <li>• <strong>condition_engine:</strong> Rule condition evaluation and logic</li>
                                <li>• <strong>enterprise_policy_templates:</strong> Pre-built policy templates</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">🔄</div>
                        <div class="feature-title">Workflow Management Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>workflow_service:</strong> Core workflow orchestration and state management</li>
                                <li>• <strong>workflow_bridge:</strong> Integration layer between workflows and actions</li>
                                <li>• <strong>workflow_approver_service:</strong> Approval routing and notifications</li>
                                <li>• <strong>approver_selector:</strong> Intelligent approver selection based on rules</li>
                                <li>• <strong>orchestration_service:</strong> Multi-workflow coordination</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">🚨</div>
                        <div class="feature-title">Alert & Monitoring Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>alert_service:</strong> Alert generation and management</li>
                                <li>• <strong>sla_monitor:</strong> SLA tracking and violation detection</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">📜</div>
                        <div class="feature-title">Compliance & Audit Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>immutable_audit_service:</strong> Tamper-proof audit logging</li>
                                <li>• <strong>data_rights_service:</strong> GDPR/CCPA data rights management</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">🔌</div>
                        <div class="feature-title">Integration & Security Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>security_bridge_service:</strong> Security tool integration layer</li>
                                <li>• <strong>mcp_governance_service:</strong> MCP protocol management</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">🗺️</div>
                        <div class="feature-title">Framework Mapping Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>mitre_mapper:</strong> MITRE ATT&CK framework mapping</li>
                                <li>• <strong>nist_mapper:</strong> NIST Cybersecurity Framework mapping</li>
                            </ul>
                        </div>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">💾</div>
                        <div class="feature-title">Data Management Services</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <strong>enterprise_batch_loader_v2:</strong> Bulk data loading (v2)</li>
                                <li>• <strong>enterprise_batch_loader:</strong> Legacy batch processing (v1)</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h3>Service Communication Patterns</h3>
                <div class="architecture-diagram">
┌─────────────────────┐
│  API Request        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ action_service      │ ← Main entry point
└──────────┬──────────┘
           │
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌─────────────────┐
│ assessment_      │  │ action_         │
│ service          │  │ taxonomy        │
│ (Risk Scoring)   │  │ (Classification)│
└──────────┬───────┘  └─────────────────┘
           │
           ▼
┌──────────────────────┐
│ condition_engine     │
│ (Rule Evaluation)    │
└──────────┬───────────┘
           │
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌─────────────────┐
│ Auto-Approve     │  │ workflow_       │
│ (Risk < 50)      │  │ service         │
│                  │  │ (Approval)      │
└──────────────────┘  └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ workflow_       │
                      │ approver_       │
                      │ service         │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ approver_       │
                      │ selector        │
                      └─────────────────┘
                </div>

                <h3>Service Performance Characteristics</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Avg Response Time</th>
                                <th>Max Load</th>
                                <th>Dependencies</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>action_service</td>
                                <td>50ms</td>
                                <td>200 req/s</td>
                                <td>Database, assessment_service</td>
                            </tr>
                            <tr>
                                <td>assessment_service</td>
                                <td><200ms</td>
                                <td>500 req/s</td>
                                <td>cvss_calculator, Database</td>
                            </tr>
                            <tr>
                                <td>workflow_service</td>
                                <td>100ms</td>
                                <td>100 req/s</td>
                                <td>Database, workflow_bridge</td>
                            </tr>
                            <tr>
                                <td>mcp_governance_service</td>
                                <td>80ms</td>
                                <td>150 req/s</td>
                                <td>action_service, Database</td>
                            </tr>
                            <tr>
                                <td>immutable_audit_service</td>
                                <td>30ms</td>
                                <td>300 req/s</td>
                                <td>Database only</td>
                            </tr>
                            <tr>
                                <td>alert_service</td>
                                <td>60ms</td>
                                <td>200 req/s</td>
                                <td>Database, WebSocket</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Deployment Tab -->
            <div id="deployment" class="tab-content">
                <h2>Deployment & Infrastructure</h2>

                <div class="alert alert-success">
                    <span class="alert-icon">🚀</span>
                    <div>
                        <strong>Production Platform:</strong> <a href="https://pilot.owkai.app" target="_blank" style="color: #065f46; font-weight: 600;">https://pilot.owkai.app</a><br>
                        <strong>AWS Region:</strong> us-east-2 (Ohio)<br>
                        <strong>AWS Account ID:</strong> 110948415588<br>
                        <strong>ECS Cluster:</strong> owkai-pilot
                    </div>
                </div>

                <h3>Infrastructure Overview</h3>
                <div class="architecture-diagram">
                                   ┌──────────────────────┐
                                   │ Route 53 DNS         │
                                   │ pilot.owkai.app      │
                                   └──────────┬───────────┘
                                              │
                                              ▼
                          ┌────────────────────────────────┐
                          │ Application Load Balancer      │
                          │ - SSL/TLS Termination          │
                          │ - Health Checks                │
                          │ - WAF (planned)                │
                          └───────────┬────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │                                           │
                ▼                                           ▼
┌───────────────────────────┐           ┌───────────────────────────┐
│ ECS Fargate Service       │           │ ECS Fargate Service       │
│ Backend (Python/FastAPI)  │           │ Frontend (React/Nginx)    │
│                           │           │                           │
│ - Tasks: 2                │           │ - Tasks: 2                │
│ - CPU: 256 (.25 vCPU)     │           │ - CPU: 256                │
│ - Memory: 512 MB          │           │ - Memory: 512 MB          │
│ - Port: 8000              │           │ - Port: 80                │
│ - Auto-scaling enabled    │           │ - Auto-scaling enabled    │
└──────────┬────────────────┘           └───────────────────────────┘
           │
           │
           ▼
┌─────────────────────────────────────┐
│ RDS PostgreSQL 15 (Multi-AZ)        │
│                                     │
│ - Instance: db.t3.medium            │
│ - Storage: 100 GB SSD (gp3)         │
│ - Encrypted at rest                 │
│ - Automated backups (7 days)        │
│ - Private subnet only               │
└─────────────────────────────────────┘

           ┌──────────────────────────┐
           │ AWS Secrets Manager      │
           │ - JWT Keys (RS256)       │
           │ - Database Credentials   │
           │ - API Keys               │
           └──────────────────────────┘

           ┌──────────────────────────┐
           │ CloudWatch               │
           │ - Logs                   │
           │ - Metrics                │
           │ - Alarms                 │
           └──────────────────────────┘

           ┌──────────────────────────┐
           │ ECR (Container Registry) │
           │ - Backend Images         │
           │ - Frontend Images        │
           └──────────────────────────┘
                </div>

                <h3>CI/CD Pipeline (GitHub Actions)</h3>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Step 1: Trigger</div>
                            <p>Automatic deployment triggered on push to <code>main</code> branch</p>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Step 2: Build & Test</div>
                            <ul>
                                <li>Run unit tests (37 tests, 90% coverage)</li>
                                <li>Security scans (CodeQL, Trivy)</li>
                                <li>Lint and type checking (Pylint, MyPy)</li>
                            </ul>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Step 3: Container Build</div>
                            <ul>
                                <li>Multi-stage Docker build for optimization</li>
                                <li>Tag with commit SHA and latest</li>
                                <li>Push to Amazon ECR (Elastic Container Registry)</li>
                            </ul>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Step 4: Deploy</div>
                            <ul>
                                <li>Update ECS task definition with new image</li>
                                <li>Rolling deployment (zero downtime)</li>
                                <li>Health check validation (30s intervals)</li>
                            </ul>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Step 5: Verify</div>
                            <ul>
                                <li>Smoke tests on production endpoints</li>
                                <li>Automatic rollback on health check failure</li>
                                <li>Notification to team via Slack (planned)</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">~5</div>
                        <div class="stat-label">Minutes Deploy Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Seconds Downtime</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">99.9%</div>
                        <div class="stat-label">Target Uptime</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">37</div>
                        <div class="stat-label">Unit Tests</div>
                    </div>
                </div>

                <h3>Performance Metrics</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Current</th>
                                <th>Target</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Average API Response Time</td>
                                <td>150ms</td>
                                <td>&lt; 200ms</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>p95 Response Time</td>
                                <td>300ms</td>
                                <td>&lt; 500ms</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>p99 Response Time</td>
                                <td>500ms</td>
                                <td>&lt; 1000ms</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>Sustained Load</td>
                                <td>100 req/sec</td>
                                <td>100+ req/sec</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>Peak Capacity</td>
                                <td>200 req/sec</td>
                                <td>200+ req/sec</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>WebSocket Connections</td>
                                <td>1000+</td>
                                <td>1000+ concurrent</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>Database Query Time</td>
                                <td>&lt;50ms avg</td>
                                <td>&lt;100ms</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                            <tr>
                                <td>Error Rate</td>
                                <td>&lt;0.5%</td>
                                <td>&lt;1%</td>
                                <td><span class="badge badge-complete">✓ Meeting</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>Monitoring & Logging</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-title">CloudWatch Logs</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• <code>/ecs/owkai-pilot-backend</code> - Backend logs</li>
                                <li>• <code>/ecs/owkai-pilot-frontend</code> - Frontend logs</li>
                                <li>• <code>/aws/rds/instance/owkai-production</code> - Database logs</li>
                            </ul>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">Custom Metrics</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• Request rate (requests/second)</li>
                                <li>• Average response time</li>
                                <li>• Error rate (4xx/5xx)</li>
                                <li>• Database connection pool usage</li>
                                <li>• Container CPU/Memory utilization</li>
                            </ul>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">Alerting</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• High error rate (>5% 5xx responses)</li>
                                <li>• Slow response time (>2s p95)</li>
                                <li>• Database connection failures</li>
                                <li>• Container health check failures</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Security Tab -->
            <div id="security" class="tab-content">
                <h2>Security & Compliance</h2>

                <div class="alert alert-warning">
                    <span class="alert-icon">🔒</span>
                    <div>
                        <strong>Security is a top priority at OW-KAI.</strong> Our platform is designed with defense-in-depth principles, 
                        implementing multiple layers of security controls to protect enterprise AI governance operations.
                    </div>
                </div>

                <h3>Authentication & Authorization</h3>
                <div class="feature-card">
                    <div class="feature-title">Cookie-Based RS256 JWT Authentication</div>
                    <div class="feature-description">
                        <ul class="feature-list">
                            <li><strong>Token Type:</strong> RS256 JWT (asymmetric signing with private/public key pairs)</li>
                            <li><strong>Storage:</strong> Secure HTTP-only cookies (protection against XSS attacks)</li>
                            <li><strong>Key Management:</strong> AWS Secrets Manager with automatic rotation every 90 days</li>
                            <li><strong>Session Timeout:</strong> 8 hours (configurable per enterprise requirements)</li>
                            <li><strong>Password Security:</strong> Bcrypt hashing with 12 salt rounds (configurable)</li>
                            <li><strong>Token Refresh:</strong> Automatic refresh before expiration with sliding window</li>
                        </ul>
                    </div>
                </div>

                <h3>Network Security</h3>
                <ul class="feature-list">
                    <li><strong>AWS VPC:</strong> Isolated virtual private cloud with private subnets for database tier</li>
                    <li><strong>Security Groups:</strong> Fine-grained firewall rules restricting access between components</li>
                    <li><strong>TLS 1.2+:</strong> All connections encrypted with modern TLS protocols (no legacy SSL)</li>
                    <li><strong>HTTPS-Only:</strong> HTTP automatically redirects to HTTPS for all traffic</li>
                    <li><strong>WAF (Planned):</strong> AWS WAF integration for protection against common web exploits</li>
                    <li><strong>DDoS Protection:</strong> AWS Shield Standard protection enabled</li>
                </ul>

                <h3>Application Security</h3>
                <ul class="feature-list">
                    <li><strong>Input Validation:</strong> Pydantic schema validation for all API inputs</li>
                    <li><strong>SQL Injection Prevention:</strong> ORM with parameterized queries (no raw SQL)</li>
                    <li><strong>XSS Protection:</strong> Content Security Policy headers and output encoding</li>
                    <li><strong>CSRF Protection:</strong> Double-submit cookie pattern with token validation</li>
                    <li><strong>Rate Limiting:</strong> Per-endpoint rate limits to prevent abuse</li>
                    <li><strong>Request Size Limits:</strong> Maximum payload size enforcement</li>
                    <li><strong>Secure Headers:</strong> HSTS, X-Frame-Options, X-Content-Type-Options</li>
                </ul>

                <h3>Data Security</h3>
                <ul class="feature-list">
                    <li><strong>At-Rest Encryption:</strong> AES-256 encryption for RDS database and ECS volumes</li>
                    <li><strong>In-Transit Encryption:</strong> TLS 1.2+ for all data transmission</li>
                    <li><strong>Secret Management:</strong> AWS Secrets Manager for credentials (no hardcoded secrets)</li>
                    <li><strong>Password Hashing:</strong> Bcrypt with salt rounds (never store plaintext)</li>
                    <li><strong>Data Minimization:</strong> No sensitive data logged to CloudWatch</li>
                    <li><strong>Secure Deletion:</strong> Cryptographic erasure for sensitive records</li>
                </ul>

                <h3>Compliance Frameworks</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Framework</th>
                                <th>Status</th>
                                <th>Key Controls</th>
                                <th>Timeline</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>SOC2 Type II</strong></td>
                                <td><span class="badge badge-progress">In Preparation</span></td>
                                <td>Access controls, audit trails, incident response, change management</td>
                                <td>Q2 2026</td>
                            </tr>
                            <tr>
                                <td><strong>GDPR</strong></td>
                                <td><span class="badge badge-complete">Implemented</span></td>
                                <td>Data processing logs, consent tracking, right to erasure, data portability</td>
                                <td>Complete</td>
                            </tr>
                            <tr>
                                <td><strong>HIPAA</strong></td>
                                <td><span class="badge badge-complete">Supported</span></td>
                                <td>PHI access logs, encryption, user attribution, audit trails</td>
                                <td>Complete</td>
                            </tr>
                            <tr>
                                <td><strong>ISO 27001</strong></td>
                                <td><span class="badge badge-progress">Aligned</span></td>
                                <td>Information security management, risk assessment, ISMS</td>
                                <td>Q3 2026</td>
                            </tr>
                            <tr>
                                <td><strong>FedRAMP</strong></td>
                                <td><span class="badge badge-planned">Planned</span></td>
                                <td>Federal government security standards</td>
                                <td>Q4 2026</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>Security Incident Response</h3>
                <div class="architecture-diagram">
┌──────────────────────┐
│ Security Event       │
│ Detection            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Alert Generation     │
│ (Real-time)          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Severity Assessment  │
│ (Critical/High/      │
│  Medium/Low)         │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────┐ ┌──────────────┐
│ Critical │ │ Non-Critical │
│ Alert    │ │ Alert        │
└────┬─────┘ └──────┬───────┘
     │              │
     ▼              ▼
┌──────────┐ ┌──────────────┐
│ Immediate│ │ Standard     │
│ Response │ │ Workflow     │
│ Team     │ │              │
│ (24/7)   │ │              │
└────┬─────┘ └──────┬───────┘
     │              │
     └──────┬───────┘
            │
            ▼
   ┌────────────────┐
   │ Investigation  │
   │ & Resolution   │
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐
   │ Post-Incident  │
   │ Review         │
   └────────────────┘
                </div>

                <h3>Security Auditing</h3>
                <p>
                    OW-KAI maintains comprehensive audit trails of all security-relevant events:
                </p>
                <ul class="feature-list">
                    <li>All authentication attempts (successful and failed) with IP address and timestamp</li>
                    <li>Authorization decisions with justification and approver attribution</li>
                    <li>Configuration changes with before/after state and user attribution</li>
                    <li>Data access patterns for anomaly detection</li>
                    <li>API calls with request/response metadata (excluding sensitive payloads)</li>
                    <li>System security events (e.g., key rotation, certificate renewal)</li>
                </ul>

                <h3>Third-Party Security</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Vendor</th>
                                <th>Purpose</th>
                                <th>Security Measures</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Amazon Web Services</td>
                                <td>Infrastructure (compute, database, storage)</td>
                                <td>SOC2, ISO 27001, FedRAMP certified; encryption at rest/in transit</td>
                            </tr>
                            <tr>
                                <td>OpenAI</td>
                                <td>Smart Rules Engine (GPT-4)</td>
                                <td>API key authentication, no sensitive data sent, rate limiting</td>
                            </tr>
                            <tr>
                                <td>GitHub</td>
                                <td>Code repository and CI/CD</td>
                                <td>OIDC authentication, branch protection, audit logs</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Business Tab -->
            <div id="business" class="tab-content">
                <h2>Business Model & Market</h2>

                <h3>Company Information</h3>
                <div class="feature-card">
                    <div class="feature-description">
                        <p><strong>Legal Entity:</strong> OW-KAI Technologies, Inc.</p>
                        <p><strong>Incorporation:</strong> Delaware C-Corporation</p>
                        <p><strong>Founded:</strong> 2025</p>
                        <p><strong>Founder & CEO:</strong> Donald King (Veteran Entrepreneur)</p>
                        <p><strong>Status:</strong> Pre-seed stage, seeking Techstars acceptance</p>
                        <p><strong>Platform:</strong> <a href="https://pilot.owkai.app" target="_blank">https://pilot.owkai.app</a></p>
                    </div>
                </div>

                <h3>Target Market</h3>
                <p>
                    <strong>Primary Market:</strong> Enterprise B2B (Fortune 500 and mid-market companies)
                </p>

                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🏦</div>
                        <div class="feature-title">Financial Services</div>
                        <div class="feature-description">
                            Banks, insurance companies, investment firms requiring strict compliance and audit trails
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏥</div>
                        <div class="feature-title">Healthcare</div>
                        <div class="feature-description">
                            Hospitals, pharmaceutical companies, health tech requiring HIPAA compliance
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💻</div>
                        <div class="feature-title">Technology</div>
                        <div class="feature-description">
                            SaaS companies, cloud providers, AI-first companies deploying agent systems
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏛️</div>
                        <div class="feature-title">Government</div>
                        <div class="feature-description">
                            Federal, state, and local agencies requiring FedRAMP and high-security standards
                        </div>
                    </div>
                </div>

                <h3>Ideal Customer Profile</h3>
                <ul class="feature-list">
                    <li><strong>Company Size:</strong> 1,000+ employees</li>
                    <li><strong>AI Agent Deployment:</strong> 50+ AI agents deployed or planned</li>
                    <li><strong>Security/Compliance Teams:</strong> Existing dedicated teams</li>
                    <li><strong>Regulatory Requirements:</strong> SOC2, GDPR, HIPAA, or similar compliance needs</li>
                    <li><strong>AI Governance Concerns:</strong> Recent incidents or proactive risk management</li>
                    <li><strong>Annual AI Security Budget:</strong> $200K-$5M allocated for AI security</li>
                </ul>

                <h3>Pricing Strategy</h3>
                <div class="pricing-grid">
                    <div class="pricing-card">
                        <div class="pricing-tier">Pilot Tier</div>
                        <div class="pricing-amount">$50K-$100K</div>
                        <div class="pricing-period">Annual Recurring Revenue</div>
                        <ul class="pricing-features">
                            <li>10-25 AI agents monitored</li>
                            <li>Basic approval workflows</li>
                            <li>Standard compliance reporting</li>
                            <li>Email & chat support</li>
                            <li>Quarterly business reviews</li>
                        </ul>
                        <p style="text-align: center; margin-top: 20px; color: var(--text-secondary);">
                            <strong>Use Case:</strong> POC and initial deployment
                        </p>
                    </div>

                    <div class="pricing-card featured">
                        <div class="pricing-tier">Enterprise Tier</div>
                        <div class="pricing-amount">$250K-$500K</div>
                        <div class="pricing-period">Annual Recurring Revenue</div>
                        <ul class="pricing-features">
                            <li>50+ AI agents monitored</li>
                            <li>Advanced approval workflows</li>
                            <li>Smart Rules Engine included</li>
                            <li>Priority support (4-hour SLA)</li>
                            <li>Dedicated success manager</li>
                            <li>Custom integrations available</li>
                            <li>Monthly business reviews</li>
                        </ul>
                        <p style="text-align: center; margin-top: 20px; color: var(--text-secondary);">
                            <strong>Use Case:</strong> Full production deployment
                        </p>
                    </div>

                    <div class="pricing-card">
                        <div class="pricing-tier">Premium Compliance</div>
                        <div class="pricing-amount">$500K-$1M+</div>
                        <div class="pricing-period">Annual Recurring Revenue</div>
                        <ul class="pricing-features">
                            <li>Unlimited AI agents</li>
                            <li>Custom compliance reporting</li>
                            <li>Audit support & consulting</li>
                            <li>24/7 premium support (1-hour SLA)</li>
                            <li>On-site training & workshops</li>
                            <li>Custom feature development</li>
                            <li>White-glove onboarding</li>
                        </ul>
                        <p style="text-align: center; margin-top: 20px; color: var(--text-secondary);">
                            <strong>Use Case:</strong> Highly regulated industries
                        </p>
                    </div>
                </div>

                <h3>Value Proposition</h3>
                <div class="alert alert-success">
                    <span class="alert-icon">💰</span>
                    <div>
                        <strong>Customer Value Calculation:</strong><br><br>
                        <strong>Customer Saves:</strong><br>
                        • $200K in manual compliance processes<br>
                        • $4.5M in potential breach risk mitigation<br>
                        • $500K in audit preparation costs<br>
                        <strong>Total Value:</strong> $5.2M annually<br><br>
                        <strong>OW-KAI Pricing:</strong> $250K-$500K<br>
                        <strong>ROI:</strong> <strong>10x+</strong> for typical enterprise customer
                    </div>
                </div>

                <h3>Revenue Projections</h3>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Q4 2025</div>
                            <p><strong>Goal:</strong> First pilot customer</p>
                            <p><strong>Revenue:</strong> $50K-$100K ARR</p>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Q2 2026</div>
                            <p><strong>Goal:</strong> Series A milestone</p>
                            <p><strong>Revenue:</strong> $250K-$500K ARR</p>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Q4 2026</div>
                            <p><strong>Goal:</strong> Scale to multiple enterprise customers</p>
                            <p><strong>Revenue:</strong> $1M+ ARR with 3-5 enterprise customers</p>
                        </div>
                    </div>
                </div>

                <h3>Go-to-Market Strategy</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-title">Phase 1: Pilot Programs (Current)</div>
                        <div class="feature-description">
                            <p><strong>Target:</strong> 3-5 enterprise pilots at $25K-$50K each</p>
                            <p><strong>Timeline:</strong> 6 months</p>
                            <p><strong>Strategy:</strong> Warm introductions via network</p>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">Phase 2: Enterprise Sales</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• Direct sales to Fortune 1000 CISOs</li>
                                <li>• Content marketing (whitepapers, case studies)</li>
                                <li>• Conference speaking (RSA, Black Hat)</li>
                                <li>• Channel partnerships</li>
                            </ul>
                        </div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">Phase 3: Scale</div>
                        <div class="feature-description">
                            <ul style="list-style: none; padding: 0; margin-top: 10px;">
                                <li>• Inside sales team</li>
                                <li>• Channel/reseller partnerships</li>
                                <li>• Strategic integrations (Salesforce, ServiceNow)</li>
                                <li>• International expansion</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h3>Competition & Differentiation</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Competitor Type</th>
                                <th>Examples</th>
                                <th>Their Approach</th>
                                <th>OW-KAI Advantage</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Traditional Cybersecurity</td>
                                <td>CrowdStrike, SentinelOne</td>
                                <td>General security, endpoint protection</td>
                                <td>Purpose-built for AI agent governance, not retrofitted</td>
                            </tr>
                            <tr>
                                <td>AI Governance Startups</td>
                                <td>Holistic AI, Credo AI</td>
                                <td>Compliance focus, post-deployment analysis</td>
                                <td>Real-time pre-execution control with HITL workflows</td>
                            </tr>
                            <tr>
                                <td>Custom In-House Solutions</td>
                                <td>Enterprise dev teams</td>
                                <td>Build from scratch</td>
                                <td>Production-ready, $500K+ cost avoidance, 6-12 month faster</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>OW-KAI Differentiation</h3>
                <ul class="feature-list">
                    <li><strong>First-Mover:</strong> Purpose-built for AI agent governance from day one</li>
                    <li><strong>Real-Time:</strong> Pre-execution risk assessment and control (not post-mortem analysis)</li>
                    <li><strong>MCP Native:</strong> Standards-based integration with Model Context Protocol</li>
                    <li><strong>Production-Ready:</strong> Live platform operational at pilot.owkai.app (not vaporware)</li>
                    <li><strong>Comprehensive:</strong> Combines monitoring, control, and compliance in one platform</li>
                    <li><strong>Veteran-Led:</strong> Trusted leadership with government and enterprise security background</li>
                </ul>

                <h3>Funding Strategy</h3>
                <div class="alert alert-info">
                    <span class="alert-icon">💵</span>
                    <div>
                        <strong>Current Status:</strong><br>
                        • Pre-revenue, pilot-ready platform<br>
                        • Clean cap table (no investors yet)<br>
                        • Applying to Techstars for 2025 cohort<br><br>
                        
                        <strong>Seed Round Target:</strong> $250K-$500K<br><br>
                        
                        <strong>Use of Funds:</strong><br>
                        • Engineering team: 3 engineers @ $120K-150K each ($360K-450K)<br>
                        • Sales & marketing: $100K-150K<br>
                        • AWS infrastructure scaling: $50K<br>
                        • Legal & compliance certifications (SOC2): $50K<br>
                        • Operating expenses: 18-month runway<br><br>
                        
                        <strong>Investor Targets:</strong><br>
                        • Techstars accelerator program<br>
                        • Enterprise/security-focused VCs<br>
                        • Angel investors with CISO connections<br>
                        • Strategic investors (cybersecurity vendors)
                    </div>
                </div>

                <h3>Market Size & Opportunity</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">$18B</div>
                        <div class="stat-label">AI Security Market by 2027</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">45%</div>
                        <div class="stat-label">CAGR 2023-2027</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">85%</div>
                        <div class="stat-label">Enterprises Using AI by 2026</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">$4.5M</div>
                        <div class="stat-label">Avg Cost of AI Incident</div>
                    </div>
                </div>
            </div>

            <!-- Roadmap Tab -->
            <div id="roadmap" class="tab-content">
                <h2>Development Roadmap</h2>

                <h3>Current Status: 95% Enterprise-Ready</h3>
                
                <div class="stats-grid">
                    <div class="stat-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                        <div class="stat-number">95%</div>
                        <div class="stat-label">Platform Complete</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                        <div class="stat-number">5%</div>
                        <div class="stat-label">Integration Testing</div>
                    </div>
                </div>

                <h3>Completed Features</h3>
                <div class="alert alert-success">
                    <span class="alert-icon">✅</span>
                    <div>
                        <strong>Operational in Production</strong>
                    </div>
                </div>
                <ul class="feature-list">
                    <li>AWS infrastructure fully deployed (ECS, RDS, ALB, CloudWatch)</li>
                    <li>Backend API with 135+ endpoints operational</li>
                    <li>Frontend React application with all major components</li>
                    <li>Cookie-based RS256 JWT authentication system</li>
                    <li>MCP action ingestion and governance</li>
                    <li>Risk assessment engine (30-100 scoring)</li>
                    <li>Smart Rules Engine with OpenAI GPT-4 integration</li>
                    <li>Real-time alert monitoring with background processing</li>
                    <li>Authorization Center UI with multi-level approvals</li>
                    <li>User management and RBAC system</li>
                    <li>Audit trail and compliance logging</li>
                    <li>CI/CD pipeline with zero-downtime deployments</li>
                </ul>

                <h3>In Progress (Testing Phase)</h3>
                <div class="alert alert-warning">
                    <span class="alert-icon">🔧</span>
                    <div>
                        <strong>Current Sprint Focus</strong>
                    </div>
                </div>
                <ul class="feature-list">
                    <li>Policy engine & workflow merge (reducing redundancy)</li>
                    <li>Frontend data integration (replacing demo data with real backend data)</li>
                    <li>Endpoint consolidation (removing duplicate APIs)</li>
                    <li>End-to-end user flow testing</li>
                    <li>Load testing under production conditions (50+ concurrent users)</li>
                    <li>Dashboard refresh rate optimization (15s → 60s)</li>
                </ul>

                <h3>Q4 2025: Pilot Readiness</h3>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Week 1-2: Integration & Bug Fixes</div>
                            <ul>
                                <li>Merge policy engine and workflow creation systems</li>
                                <li>Fix dashboard data integration issues</li>
                                <li>Consolidate redundant API endpoints</li>
                                <li>Optimize frontend refresh rates</li>
                            </ul>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Week 3-4: Testing & Validation</div>
                            <ul>
                                <li>End-to-end user flow testing</li>
                                <li>Load testing (simulate 50+ concurrent users)</li>
                                <li>Security penetration testing</li>
                                <li>Performance optimization</li>
                            </ul>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-date">Week 5-6: Pilot Launch</div>
                            <ul>
                                <li>Onboard first 1-3 pilot customers</li>
                                <li>Implement customer feedback loop</li>
                                <li>Document deployment process</li>
                                <li>Create customer success playbooks</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h3>Q1 2026: Feature Enhancement</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-title">January 2026</div>
                        <ul style="list-style: none; padding: 0; margin-top: 10px;">
                            <li>• SSO integration (Okta, Azure AD)</li>
                            <li>• Enhanced audit reporting</li>
                            <li>• Custom compliance templates</li>
                            <li>• Advanced analytics dashboard</li>
                        </ul>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">February 2026</div>
                        <ul style="list-style: none; padding: 0; margin-top: 10px;">
                            <li>• Slack/PagerDuty integrations</li>
                            <li>• Multi-tenancy architecture</li>
                            <li>• API rate limiting improvements</li>
                            <li>• Mobile-responsive enhancements</li>
                        </ul>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">March 2026</div>
                        <ul style="list-style: none; padding: 0; margin-top: 10px;">
                            <li>• ServiceNow ticketing integration</li>
                            <li>• Advanced ML anomaly detection</li>
                            <li>• GraphQL API layer</li>
                            <li>• International compliance (EU GDPR)</li>
                        </ul>
                    </div>
                </div>

                <h3>Q2 2026: Scale & Growth</h3>
                <ul class="feature-list">
                    <li>Scale to 5-10 enterprise customers</li>
                    <li>Build sales & customer success team</li>
                    <li>SOC2 Type II certification completed</li>
                    <li>Expand AWS infrastructure (multi-region deployment)</li>
                    <li>Launch partner program</li>
                    <li>Establish advisory board with CISOs</li>
                </ul>

                <h3>Q3-Q4 2026: Enterprise Features</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-title">Advanced Capabilities</div>
                        <ul style="list-style: none; padding: 0; margin-top: 10px;">
                            <li>• Advanced workflow orchestration</li>
                            <li>• Custom ML risk models per customer</li>
                            <li>• Federal compliance (FedRAMP)</li>
                            <li>• Mobile applications (iOS/Android)</li>
                        </ul>
                    </div>
                    <div class="feature-card">
                        <div class="feature-title">Geographic Expansion</div>
                        <ul style="list-style: none; padding: 0; margin-top: 10px;">
                            <li>• EU data residency (Ireland region)</li>
                            <li>• APAC expansion (Singapore region)</li>
                            <li>• Localization for EU/APAC markets</li>
                            <li>• International compliance frameworks</li>
                        </ul>
                    </div>
                </div>

                <h3>Planned Integrations</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Integration</th>
                                <th>Type</th>
                                <th>Timeline</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Okta</td>
                                <td>SSO / Identity</td>
                                <td>Q1 2026</td>
                                <td>Enterprise authentication</td>
                            </tr>
                            <tr>
                                <td>Azure AD</td>
                                <td>SSO / Identity</td>
                                <td>Q1 2026</td>
                                <td>Microsoft ecosystem integration</td>
                            </tr>
                            <tr>
                                <td>Slack</td>
                                <td>Notifications</td>
                                <td>Q1 2026</td>
                                <td>Real-time team alerts</td>
                            </tr>
                            <tr>
                                <td>PagerDuty</td>
                                <td>Incident Management</td>
                                <td>Q1 2026</td>
                                <td>Critical alert escalation</td>
                            </tr>
                            <tr>
                                <td>ServiceNow</td>
                                <td>ITSM</td>
                                <td>Q1 2026</td>
                                <td>Ticketing and workflow integration</td>
                            </tr>
                            <tr>
                                <td>Splunk</td>
                                <td>SIEM</td>
                                <td>Q2 2026</td>
                                <td>Security event correlation</td>
                            </tr>
                            <tr>
                                <td>Salesforce</td>
                                <td>CRM</td>
                                <td>Q3 2026</td>
                                <td>Customer data integration</td>
                            </tr>
                            <tr>
                                <td>Jira</td>
                                <td>Project Management</td>
                                <td>Q3 2026</td>
                                <td>Issue tracking integration</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h3>Long-Term Vision (2027+)</h3>
                <div class="alert alert-info">
                    <span class="alert-icon">🚀</span>
                    <div>
                        <strong>Strategic Goals for 2027 and Beyond:</strong><br><br>
                        • Become the <strong>de facto standard</strong> for enterprise AI agent governance<br>
                        • Expand to <strong>50+ enterprise customers</strong> across multiple verticals<br>
                        • Achieve <strong>$10M+ ARR</strong> milestone<br>
                        • Launch <strong>AI governance certification program</strong> for enterprises<br>
                        • Establish <strong>industry partnerships</strong> with major AI platform providers<br>
                        • Open source <strong>community edition</strong> for smaller organizations<br>
                        • Build <strong>ecosystem marketplace</strong> for third-party integrations
                    </div>
                </div>
            </div>

        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>OW-KAI Technologies, Inc.</h3>
                    <p>Enterprise AI Agent Governance Platform</p>
                    <p>Delaware C-Corporation</p>
                    <p>Founded 2025</p>
                </div>
                <div class="footer-section">
                    <h3>Resources</h3>
                    <ul>
                        <li><a href="https://pilot.owkai.app" target="_blank">Production Platform</a></li>
                        <li><a href="https://pilot.owkai.app/docs" target="_blank">API Documentation</a></li>
                        <li><a href="https://github.com/Amplify-Cost/owkai-pilot-backend" target="_blank">Backend Repository</a></li>
                        <li><a href="https://github.com/Amplify-Cost/owkai-pilot-frontend" target="_blank">Frontend Repository</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Platform Stats</h3>
                    <ul>
                        <li>135+ API Endpoints</li>
                        <li>18 Database Tables</li>
                        <li>29 Route Modules</li>
                        <li>24 Backend Services</li>
                        <li>95% Enterprise Ready</li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Infrastructure</h3>
                    <ul>
                        <li>AWS us-east-2 (Ohio)</li>
                        <li>Account: 110948415588</li>
                        <li>ECS Cluster: owkai-pilot</li>
                        <li>PostgreSQL 15 Multi-AZ</li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>
                    Documentation Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
                    Version 2.0 - Enhanced Edition | All Rights Reserved © 2025 OW-KAI Technologies, Inc.
                </p>
            </div>
        </div>

    </div>

    <script>
        function showTab(tabName) {{
            // Hide all tab contents
            const contents = document.getElementsByClassName('tab-content');
            for (let content of contents) {{
                content.classList.remove('active');
            }}
            
            // Remove active class from all tabs
            const tabs = document.getElementsByClassName('nav-tab');
            for (let tab of tabs) {{
                tab.classList.remove('active');
            }}
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Smooth scroll to top of content
            document.querySelector('.content-area').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        
        // Add smooth scrolling for internal links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
    </script>
</body>
</html>"""
    
    return html_content


def main():
    """Main execution function"""
    
    print("📝 Generating enhanced OW-KAI Technologies documentation...")
    print("")
    
    # Create enterprise-docs directory
    docs_dir = "enterprise-docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # Generate comprehensive HTML documentation
    print("✅ Creating comprehensive index.html")
    html_content = create_enhanced_documentation()
    with open(f"{docs_dir}/index.html", "w") as f:
        f.write(html_content)
    
    print("")
    print("✅ Enhanced documentation generated successfully!")
    print(f"   - {docs_dir}/index.html (Comprehensive interactive documentation)")
    print("")
    print("✅ Documentation now reflects OW-KAI Technologies, Inc. with full enterprise detail")
    print("")
    print("📊 Documentation includes:")
    print("   - 10 comprehensive tabs with detailed content")
    print("   - Professional enterprise-grade styling")
    print("   - Complete technical specifications")
    print("   - Business model and pricing information")
    print("   - Development roadmap and timelines")
    print("   - All 135+ API endpoints documented")
    print("   - 18 database tables with relationships")
    print("   - 24 backend services explained")
    print("   - Security and compliance details")


if __name__ == "__main__":
    main()
