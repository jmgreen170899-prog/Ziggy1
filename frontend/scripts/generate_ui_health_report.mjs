#!/usr/bin/env node

import { promises as fs } from 'fs';
import path from 'path';

async function generateUIHealthReport() {
  const artifactsDir = path.join(process.cwd(), 'artifacts', 'ui');
  const frontendArtifactsDir = path.join(process.cwd(), 'artifacts', 'frontend');
  
  try {
    // Load audit results
    const uiAuditPath = path.join(artifactsDir, 'ui_audit_results.json');
    const lighthouseSummaryPath = path.join(artifactsDir, 'lighthouse_summary.json');
    const jscpdReportPath = path.join(frontendArtifactsDir, 'jscpd-report.json');
    
    let uiAuditResults = [];
    let lighthouseResults = [];
    let duplicationData = null;
    
    try {
      const uiAuditContent = await fs.readFile(uiAuditPath, 'utf-8');
      uiAuditResults = JSON.parse(uiAuditContent);
    } catch (error) {
      console.warn('UI audit results not found:', error.message);
    }
    
    try {
      const lighthouseContent = await fs.readFile(lighthouseSummaryPath, 'utf-8');
      lighthouseResults = JSON.parse(lighthouseContent);
    } catch (error) {
      console.warn('Lighthouse results not found:', error.message);
    }
    
    try {
      const jscpdContent = await fs.readFile(jscpdReportPath, 'utf-8');
      duplicationData = JSON.parse(jscpdContent);
    } catch (error) {
      console.warn('JSCPD results not found:', error.message);
    }

    // Generate report
    const report = generateReport(uiAuditResults, lighthouseResults, duplicationData);
    
    // Save report
    const reportPath = path.join(process.cwd(), 'UI_HEALTH_REPORT.md');
    await fs.writeFile(reportPath, report);
    
    console.log(`✓ UI Health Report generated: ${reportPath}`);
    
    return report;
  } catch (error) {
    console.error('Failed to generate UI health report:', error);
    throw error;
  }
}

function generateReport(uiAuditResults, lighthouseResults, duplicationData) {
  const timestamp = new Date().toISOString();
  
  let report = `# UI Health Report

Generated: ${timestamp}

## Executive Summary

`;

  // Calculate overall health scores
  const totalRoutes = uiAuditResults.length;
  const successfulRoutes = uiAuditResults.filter(r => r.status === 'success').length;
  const failedRoutes = uiAuditResults.filter(r => r.status === 'error').length;
  
  const avgPerformance = lighthouseResults.length > 0 ? 
    Math.round(lighthouseResults.reduce((sum, r) => sum + (r.scores?.performance || 0), 0) / lighthouseResults.length) : 0;
  const avgAccessibility = lighthouseResults.length > 0 ? 
    Math.round(lighthouseResults.reduce((sum, r) => sum + (r.scores?.accessibility || 0), 0) / lighthouseResults.length) : 0;

  report += `- **Routes Tested**: ${totalRoutes}
- **Successful**: ${successfulRoutes} ✅
- **Failed**: ${failedRoutes} ❌
- **Average Performance Score**: ${avgPerformance}%
- **Average Accessibility Score**: ${avgAccessibility}%

`;

  // P0 Issues (Critical)
  const p0Issues = [];
  
  uiAuditResults.forEach(result => {
    if (result.status === 'error') {
      p0Issues.push(`🚨 **${result.route}**: Route completely broken - ${result.error}`);
    }
    if (result.metrics?.consoleErrors?.length > 0) {
      p0Issues.push(`🚨 **${result.route}**: ${result.metrics.consoleErrors.length} console errors`);
    }
    if (result.metrics?.networkErrors?.length > 0) {
      p0Issues.push(`🚨 **${result.route}**: ${result.metrics.networkErrors.length} network errors`);
    }
    if (result.metrics?.nanCells > 0) {
      p0Issues.push(`🚨 **${result.route}**: ${result.metrics.nanCells} NaN values in UI`);
    }
  });

  lighthouseResults.forEach(result => {
    if (result.scores?.performance < 30) {
      p0Issues.push(`🚨 **${result.route}**: Critical performance issues (${result.scores.performance}%)`);
    }
    if (result.scores?.accessibility < 50) {
      p0Issues.push(`🚨 **${result.route}**: Critical accessibility issues (${result.scores.accessibility}%)`);
    }
  });

  report += `## 🚨 P0 Issues (Critical - Fix Immediately)

${p0Issues.length === 0 ? '✅ No P0 issues found!' : p0Issues.map(issue => `- ${issue}`).join('\\n')}

`;

  // P1 Issues (High Priority)
  const p1Issues = [];
  
  uiAuditResults.forEach(result => {
    if (result.metrics?.missingFields?.length > 0) {
      p1Issues.push(`⚠️ **${result.route}**: ${result.metrics.missingFields.length} missing/empty fields`);
    }
    if (result.metrics?.staleBadges > 0) {
      p1Issues.push(`⚠️ **${result.route}**: ${result.metrics.staleBadges} stale data indicators`);
    }
  });

  lighthouseResults.forEach(result => {
    if (result.scores?.performance >= 30 && result.scores?.performance < 70) {
      p1Issues.push(`⚠️ **${result.route}**: Performance needs improvement (${result.scores.performance}%)`);
    }
    if (result.scores?.accessibility >= 50 && result.scores?.accessibility < 80) {
      p1Issues.push(`⚠️ **${result.route}**: Accessibility needs improvement (${result.scores.accessibility}%)`);
    }
    if (result.metrics?.cumulativeLayoutShift > 0.1) {
      p1Issues.push(`⚠️ **${result.route}**: High layout shift (${result.metrics.cumulativeLayoutShift})`);
    }
  });

  report += `## ⚠️ P1 Issues (High Priority)

${p1Issues.length === 0 ? '✅ No P1 issues found!' : p1Issues.map(issue => `- ${issue}`).join('\\n')}

`;

  // P2 Issues (Polish)
  const p2Issues = [];
  
  if (duplicationData && duplicationData.duplicates?.length > 0) {
    p2Issues.push(`📝 **Code Duplication**: ${duplicationData.duplicates.length} duplicate code blocks found`);
  }

  uiAuditResults.forEach(result => {
    if (result.metrics?.loadTime > 5000) {
      p2Issues.push(`📝 **${result.route}**: Slow load time (${Math.round(result.metrics.loadTime)}ms)`);
    }
  });

  report += `## 📝 P2 Issues (Polish & Optimization)

${p2Issues.length === 0 ? '✅ No P2 issues found!' : p2Issues.map(issue => `- ${issue}`).join('\\n')}

`;

  // Detailed Route Analysis
  report += `## 📊 Detailed Route Analysis

| Route | Status | Performance | A11y | Console Errors | Network Errors | Data Issues |
|-------|--------|-------------|------|----------------|----------------|-------------|
`;

  uiAuditResults.forEach(result => {
    const lighthouse = lighthouseResults.find(lr => lr.route === result.route);
    const perfScore = lighthouse?.scores?.performance || 'N/A';
    const a11yScore = lighthouse?.scores?.accessibility || 'N/A';
    const consoleErrors = result.metrics?.consoleErrors?.length || 0;
    const networkErrors = result.metrics?.networkErrors?.length || 0;
    const dataIssues = (result.metrics?.nanCells || 0) + (result.metrics?.infinityCells || 0) + (result.metrics?.missingFields?.length || 0);
    
    const statusIcon = result.status === 'success' ? '✅' : '❌';
    
    report += `| ${result.route} | ${statusIcon} | ${perfScore}% | ${a11yScore}% | ${consoleErrors} | ${networkErrors} | ${dataIssues} |\\n`;
  });

  // Screenshots
  report += `
## 📸 Screenshots

Route screenshots are available in \`artifacts/ui/\`:

`;

  uiAuditResults.forEach(result => {
    if (result.screenshot) {
      report += `- [${result.route}](artifacts/ui/${result.screenshot})\\n`;
    }
  });

  // Action Items
  report += `
## ✅ Action Items Checklist

### Immediate (P0)
`;

  p0Issues.forEach((issue, index) => {
    report += `- [ ] **P0-${index + 1}**: ${issue.replace(/🚨 \*\*[^*]+\*\*: /, '')}\\n`;
  });

  report += `
### High Priority (P1)
`;

  p1Issues.forEach((issue, index) => {
    report += `- [ ] **P1-${index + 1}**: ${issue.replace(/⚠️ \*\*[^*]+\*\*: /, '')}\\n`;
  });

  report += `
### Polish (P2)
`;

  p2Issues.forEach((issue, index) => {
    report += `- [ ] **P2-${index + 1}**: ${issue.replace(/📝 \*\*[^*]+\*\*: /, '')}\\n`;
  });

  // Artifacts Links
  report += `
## 📁 Artifacts

- [Full UI Audit Results](artifacts/ui/ui_audit_results.json)
- [Lighthouse Summary](artifacts/ui/lighthouse_summary.json)
- [Playwright Report](artifacts/ui/playwright-report/index.html)
${duplicationData ? '- [Code Duplication Report](artifacts/frontend/jscpd-report.json)' : ''}

## 🎯 Success Criteria

✅ **Ready for Production When:**
- [ ] Zero P0 issues
- [ ] Zero P1 console/network errors  
- [ ] All routes load successfully with data
- [ ] Performance scores > 70% average
- [ ] Accessibility scores > 80% average
- [ ] TTL badges properly indicate data freshness

---

*This report was generated automatically by the UI Health Audit system.*
`;

  return report;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  generateUIHealthReport().catch(console.error);
}

export default generateUIHealthReport;