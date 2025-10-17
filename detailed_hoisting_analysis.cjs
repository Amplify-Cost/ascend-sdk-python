#!/usr/bin/env node

/**
 * Detailed JavaScript Hoisting Analysis for AgentAuthorizationDashboard.jsx
 * Focuses on actual hoisting behavior in React components
 */

const fs = require('fs');

const DASHBOARD_FILE = '/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx';

class DetailedHoistingAnalysis {
  constructor(filePath) {
    this.filePath = filePath;
    this.content = fs.readFileSync(filePath, 'utf8');
    this.lines = this.content.split('\n');
    this.report = {
      critical_issues: [],
      warnings: [],
      validations: [],
      performance_notes: []
    };
  }

  // Critical Issue 1: Function Expression Hoisting in React Components
  analyzeFunctionExpressionHoisting() {
    console.log('\n🔍 1. FUNCTION EXPRESSION HOISTING ANALYSIS');
    console.log('='.repeat(70));
    
    // In React components, const declarations are NOT hoisted like function declarations
    // This can cause "Cannot access before initialization" errors
    
    const componentStart = this.findLineNumber(/const AgentAuthorizationDashboard/);
    const fetchPoliciesDeclaration = this.findLineNumber(/const fetchPolicies = useCallback/);
    const fetchPoliciesUsages = this.findAllLineNumbers(/fetchPolicies\(\)/);
    
    console.log(`Component starts at line: ${componentStart}`);
    console.log(`fetchPolicies declared at line: ${fetchPoliciesDeclaration}`);
    console.log(`fetchPolicies called at lines: ${fetchPoliciesUsages.join(', ')}`);
    
    // Check if any usage occurs before declaration WITHIN the component
    const problematicUsages = fetchPoliciesUsages.filter(usage => 
      usage > componentStart && usage < fetchPoliciesDeclaration
    );
    
    if (problematicUsages.length > 0) {
      this.report.critical_issues.push({
        issue: 'Temporal Dead Zone Violation',
        description: `fetchPolicies used before declaration at lines: ${problematicUsages.join(', ')}`,
        severity: 'HIGH',
        solution: 'Move fetchPolicies declaration before first usage or use function declaration instead'
      });
      console.log(`❌ CRITICAL: Temporal Dead Zone violation at lines: ${problematicUsages.join(', ')}`);
    } else {
      this.report.validations.push('✅ fetchPolicies properly declared before usage');
      console.log('✅ fetchPolicies properly declared before usage');
    }
    
    return problematicUsages.length === 0;
  }

  // Critical Issue 2: useEffect Dependencies and Closure Issues  
  analyzeUseEffectClosures() {
    console.log('\n🔄 2. USEEFFECT CLOSURE AND DEPENDENCY ANALYSIS');
    console.log('='.repeat(70));
    
    // Find the main useEffect that uses fetchPolicies
    const useEffectStart = this.findLineNumber(/useEffect\(\(\) => {/);
    const useEffectEnd = this.findLineNumber(/\], \[/, useEffectStart);
    
    if (useEffectStart > 0 && useEffectEnd > 0) {
      const useEffectContent = this.lines.slice(useEffectStart - 1, useEffectEnd).join('\n');
      const dependencyArray = this.extractDependencyArray();
      
      console.log(`useEffect found at lines ${useEffectStart}-${useEffectEnd}`);
      console.log(`Dependencies: [${dependencyArray.join(', ')}]`);
      
      // Check if all used functions are in dependency array
      const functionsUsed = this.extractFunctionsFromUseEffect(useEffectContent);
      const missingDependencies = functionsUsed.filter(func => !dependencyArray.includes(func));
      
      if (missingDependencies.length > 0) {
        this.report.warnings.push({
          issue: 'Missing useEffect Dependencies',
          description: `Functions used but not in dependency array: ${missingDependencies.join(', ')}`,
          severity: 'MEDIUM'
        });
        console.log(`⚠️  Missing dependencies: ${missingDependencies.join(', ')}`);
      } else {
        this.report.validations.push('✅ All useEffect dependencies properly declared');
        console.log('✅ All useEffect dependencies properly declared');
      }
      
      return missingDependencies.length === 0;
    }
    
    return false;
  }

  // Critical Issue 3: useCallback Dependency Analysis
  analyzeUseCallbackDependencies() {
    console.log('\n📝 3. USECALLBACK DEPENDENCY ANALYSIS');
    console.log('='.repeat(70));
    
    const useCallbacks = this.findAllUseCallbacks();
    let validCallbacks = 0;
    let problematicCallbacks = [];
    
    useCallbacks.forEach(callback => {
      const dependencies = this.extractCallbackDependencies(callback.name);
      const usedVariables = this.extractVariablesFromCallback(callback.name);
      
      const missingDeps = usedVariables.filter(variable => 
        !dependencies.includes(variable) && 
        this.isExternalVariable(variable)
      );
      
      if (missingDeps.length > 0) {
        problematicCallbacks.push({
          name: callback.name,
          line: callback.line,
          missing: missingDeps
        });
        console.log(`❌ ${callback.name} (line ${callback.line}): missing deps [${missingDeps.join(', ')}]`);
      } else {
        validCallbacks++;
        console.log(`✅ ${callback.name} (line ${callback.line}): dependencies correct`);
      }
    });
    
    if (problematicCallbacks.length > 0) {
      this.report.warnings.push({
        issue: 'useCallback Dependency Issues',
        description: `${problematicCallbacks.length} callbacks have missing dependencies`,
        details: problematicCallbacks
      });
    } else {
      this.report.validations.push('✅ All useCallback dependencies properly managed');
    }
    
    console.log(`\n📊 Summary: ${validCallbacks}/${useCallbacks.length} callbacks have correct dependencies`);
    return problematicCallbacks.length === 0;
  }

  // Performance Issue: Render Loop Detection
  detectInfiniteRenderLoops() {
    console.log('\n🔁 4. INFINITE RENDER LOOP DETECTION');
    console.log('='.repeat(70));
    
    const potentialLoops = [];
    
    // Check for object creation in render
    const objectCreationInRender = this.findAllLineNumbers(/\{\s*\.\.\./);
    if (objectCreationInRender.length > 5) {
      potentialLoops.push('Object spread in render may cause re-renders');
    }
    
    // Check for array creation in render
    const arrayCreationInRender = this.findAllLineNumbers(/\[\s*\.\.\./);
    if (arrayCreationInRender.length > 3) {
      potentialLoops.push('Array spread in render may cause re-renders');
    }
    
    // Check for inline function creation
    const inlineFunctions = this.findAllLineNumbers(/onClick=\{.*=>/);
    if (inlineFunctions.length > 10) {
      potentialLoops.push('Inline arrow functions in JSX may cause re-renders');
    }
    
    console.log(`Object spreads in render: ${objectCreationInRender.length}`);
    console.log(`Array spreads in render: ${arrayCreationInRender.length}`);
    console.log(`Inline functions: ${inlineFunctions.length}`);
    
    if (potentialLoops.length > 0) {
      this.report.performance_notes.push({
        issue: 'Potential Render Loop Sources',
        details: potentialLoops
      });
      console.log(`⚠️  Potential render issues: ${potentialLoops.length}`);
    } else {
      this.report.validations.push('✅ No obvious infinite render loop patterns detected');
      console.log('✅ No obvious infinite render loop patterns detected');
    }
    
    return potentialLoops.length === 0;
  }

  // Component Mounting and Error Testing
  validateComponentStructure() {
    console.log('\n🏗️ 5. COMPONENT STRUCTURE VALIDATION');
    console.log('='.repeat(70));
    
    const hasErrorBoundary = this.content.includes('ErrorBoundary');
    const hasProperImports = this.content.includes('useCallback') && this.content.includes('useEffect');
    const hasExportDefault = this.content.includes('export default');
    const hasSuspenseBoundary = this.content.includes('Suspense') || this.content.includes('loading');
    
    console.log(`Error Boundary: ${hasErrorBoundary ? '✅' : '❌'}`);
    console.log(`Proper React imports: ${hasProperImports ? '✅' : '❌'}`);
    console.log(`Export default: ${hasExportDefault ? '✅' : '❌'}`);
    console.log(`Loading states: ${hasSuspenseBoundary ? '✅' : '❌'}`);
    
    const structureValid = hasErrorBoundary && hasProperImports && hasExportDefault;
    
    if (!structureValid) {
      this.report.critical_issues.push({
        issue: 'Component Structure Problems',
        description: 'Missing essential component structure elements'
      });
    } else {
      this.report.validations.push('✅ Component structure supports proper mounting');
    }
    
    return structureValid;
  }

  // Helper Methods
  findLineNumber(pattern, startLine = 0) {
    for (let i = startLine; i < this.lines.length; i++) {
      if (pattern.test(this.lines[i])) return i + 1;
    }
    return -1;
  }

  findAllLineNumbers(pattern) {
    const results = [];
    for (let i = 0; i < this.lines.length; i++) {
      if (pattern.test(this.lines[i])) results.push(i + 1);
    }
    return results;
  }

  findAllUseCallbacks() {
    const callbacks = [];
    const pattern = /const\s+(\w+)\s*=\s*useCallback/g;
    let match;
    
    while ((match = pattern.exec(this.content)) !== null) {
      const line = this.content.substring(0, match.index).split('\n').length;
      callbacks.push({ name: match[1], line: line });
    }
    
    return callbacks;
  }

  extractDependencyArray() {
    const match = this.content.match(/\], \[\s*([^\]]*)\s*\]\);/);
    if (match) {
      return match[1]
        .split(',')
        .map(dep => dep.trim().replace(/['"]/g, ''))
        .filter(dep => dep.length > 0);
    }
    return [];
  }

  extractFunctionsFromUseEffect(useEffectContent) {
    const functionCalls = useEffectContent.match(/\b(\w+)\(\)/g) || [];
    return [...new Set(functionCalls.map(call => call.replace('()', '')))];
  }

  extractCallbackDependencies(callbackName) {
    const pattern = new RegExp(`const ${callbackName} = useCallback[\\s\\S]*?\\], \\[([^\\]]*)\\]`, 'g');
    const match = pattern.exec(this.content);
    
    if (match) {
      return match[1]
        .split(',')
        .map(dep => dep.trim())
        .filter(dep => dep.length > 0);
    }
    return [];
  }

  extractVariablesFromCallback(callbackName) {
    // Simplified extraction - would need more sophisticated parsing for production
    const pattern = new RegExp(`const ${callbackName} = useCallback[\\s\\S]*?\\}, \\[`, 'g');
    const match = pattern.exec(this.content);
    
    if (match) {
      const variables = match[0].match(/\b[A-Za-z_$][A-Za-z0-9_$]*\b/g) || [];
      return [...new Set(variables)].filter(variable => 
        !['const', 'useCallback', 'async', 'await', 'try', 'catch', 'if', 'else', 'return'].includes(variable)
      );
    }
    return [];
  }

  isExternalVariable(variable) {
    // Check if variable is likely from props, state, or external scope
    const externalPatterns = ['API_BASE_URL', 'getAuthHeaders', 'set[A-Z]', 'user', 'activeTab'];
    return externalPatterns.some(pattern => new RegExp(pattern).test(variable));
  }

  // Main Analysis Runner
  runDetailedAnalysis() {
    console.log('🔬 DETAILED JAVASCRIPT HOISTING ANALYSIS');
    console.log('='.repeat(80));
    console.log(`File: ${this.filePath}`);
    console.log(`Size: ${(this.content.length / 1024).toFixed(1)} KB`);
    
    const results = {
      hoisting: this.analyzeFunctionExpressionHoisting(),
      useEffect: this.analyzeUseEffectClosures(),
      useCallback: this.analyzeUseCallbackDependencies(),
      renderLoops: this.detectInfiniteRenderLoops(),
      structure: this.validateComponentStructure()
    };

    console.log('\n📋 DETAILED FINDINGS SUMMARY');
    console.log('='.repeat(70));
    
    if (this.report.critical_issues.length > 0) {
      console.log('\n🚨 CRITICAL ISSUES:');
      this.report.critical_issues.forEach((issue, i) => {
        console.log(`${i + 1}. ${issue.issue}: ${issue.description}`);
        if (issue.solution) console.log(`   Solution: ${issue.solution}`);
      });
    }
    
    if (this.report.warnings.length > 0) {
      console.log('\n⚠️  WARNINGS:');
      this.report.warnings.forEach((warning, i) => {
        console.log(`${i + 1}. ${warning.issue}: ${warning.description}`);
      });
    }
    
    if (this.report.validations.length > 0) {
      console.log('\n✅ SUCCESSFUL VALIDATIONS:');
      this.report.validations.forEach(validation => {
        console.log(`  ${validation}`);
      });
    }
    
    if (this.report.performance_notes.length > 0) {
      console.log('\n⚡ PERFORMANCE NOTES:');
      this.report.performance_notes.forEach(note => {
        console.log(`  ${note.issue}: ${note.details ? note.details.join(', ') : 'See details above'}`);
      });
    }
    
    const criticalCount = this.report.critical_issues.length;
    const warningCount = this.report.warnings.length;
    const validationCount = this.report.validations.length;
    
    const score = validationCount / (validationCount + criticalCount + warningCount) * 100;
    const status = criticalCount === 0 ? (warningCount === 0 ? '🟢 READY' : '🟡 MINOR ISSUES') : '🔴 NEEDS FIXES';
    
    console.log(`\n🎯 FINAL ASSESSMENT:`);
    console.log(`   Score: ${score.toFixed(1)}%`);
    console.log(`   Status: ${status}`);
    console.log(`   Critical Issues: ${criticalCount}`);
    console.log(`   Warnings: ${warningCount}`);
    console.log(`   Validations Passed: ${validationCount}`);
    
    return {
      score: score,
      status: status.includes('READY'),
      report: this.report,
      results: results
    };
  }
}

// Run the detailed analysis
const analyzer = new DetailedHoistingAnalysis(DASHBOARD_FILE);
const results = analyzer.runDetailedAnalysis();

// Exit with appropriate code
process.exit(results.status ? 0 : 1);