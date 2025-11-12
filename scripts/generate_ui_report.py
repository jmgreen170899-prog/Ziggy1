#!/usr/bin/env python3
"""
ZiggyAI UI Improvements Report Generator

Reads Playwright and Lighthouse audit outputs and generates a comprehensive
ui_improvements.md with prioritized fixes, screenshots, and actionable recommendations.
"""

import json
import sys
from datetime import datetime
from typing import Any


def load_json_file(filepath: str) -> dict[str, Any] | None:
    """Load JSON file with error handling."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def get_priority_tag(issue_type: str, severity: str, count: int) -> str:
    """Determine priority tag based on issue type and severity."""
    if issue_type in ["nanValues", "overflowElements", "consoleErrors"]:
        return "P0" if count > 0 else "P2"
    elif issue_type in ["missingFields", "staleTimestamps", "hiddenElements"]:
        return "P1" if count > 2 else "P2"
    elif issue_type in ["emptyStates", "responsiveIssues"]:
        return "P2"
    else:
        return "P2"


def format_lighthouse_score(score: float) -> str:
    """Format Lighthouse score with color indicators."""
    if score >= 90:
        return f"🟢 {score}%"
    elif score >= 50:
        return f"🟡 {score}%"
    else:
        return f"🔴 {score}%"


def format_load_time(ms: float) -> str:
    """Format load time with performance indicators."""
    if ms < 1000:
        return f"🟢 {ms:.0f}ms"
    elif ms < 3000:
        return f"🟡 {ms:.0f}ms"
    else:
        return f"🔴 {ms:.0f}ms"


def generate_tab_section(
    tab_data: dict[str, Any], lighthouse_data: dict[str, Any] | None = None
) -> str:
    """Generate markdown section for a single tab."""
    tab_name = tab_data.get("tabName", "Unknown")
    route = tab_data.get("route", "/")

    # Calculate total issues
    data_metrics = tab_data.get("dataMetrics", {})
    layout_issues = tab_data.get("layoutIssues", {})
    console_errors = tab_data.get("consoleErrors", [])

    total_issues = (
        len(data_metrics.get("missingFields", []))
        + len(data_metrics.get("nanValues", []))
        + len(data_metrics.get("staleTimestamps", []))
        + len(data_metrics.get("emptyStates", []))
        + len(layout_issues.get("overflowElements", []))
        + len(layout_issues.get("hiddenElements", []))
        + len(layout_issues.get("responsiveIssues", []))
        + len(console_errors)
    )

    # Determine overall status
    critical_issues = len(data_metrics.get("nanValues", [])) + len(
        layout_issues.get("overflowElements", [])
    )
    status_icon = "🔴" if critical_issues > 0 else "🟡" if total_issues > 5 else "🟢"

    section = f"""
## {status_icon} {tab_name} (`{route}`)

**Screenshot:** `artifacts/ui/{tab_name.lower()}.png`

### 📊 What's Shown (Live Data)
- **Data Cards:** {data_metrics.get('dataCards', 0)}
- **Data Rows:** {data_metrics.get('dataRows', 0)}
- **Total Elements:** {data_metrics.get('totalElements', 0)}
- **Load Times:** DOM: {format_load_time(tab_data.get('loadTimes', {}).get('domContentLoaded', 0))}, Data: {format_load_time(tab_data.get('loadTimes', {}).get('dataLoaded', 0))}
"""

    # Add Lighthouse scores if available
    if lighthouse_data:
        scores = lighthouse_data.get("scores", {})
        section += f"""
### 🎯 Performance Scores
- **Performance:** {format_lighthouse_score(scores.get('performance', 0))}
- **Accessibility:** {format_lighthouse_score(scores.get('accessibility', 0))}
- **Best Practices:** {format_lighthouse_score(scores.get('bestPractices', 0))}
- **SEO:** {format_lighthouse_score(scores.get('seo', 0))}
"""

    # Issues detected section
    section += f"\n### ⚠️ Issues Detected ({total_issues} total)\n"

    if total_issues == 0:
        section += "✅ No issues detected - tab is performing well!\n"
        return section

    # Data Quality Issues
    if data_metrics.get("nanValues"):
        priority = get_priority_tag("nanValues", "critical", len(data_metrics["nanValues"]))
        section += (
            f"\n**{priority} - NaN/Undefined Values** ({len(data_metrics['nanValues'])} found)\n"
        )
        for value in data_metrics["nanValues"][:3]:  # Show first 3
            section += f"- {value}\n"
        if len(data_metrics["nanValues"]) > 3:
            section += f"- ... and {len(data_metrics['nanValues']) - 3} more\n"

    if data_metrics.get("missingFields"):
        priority = get_priority_tag("missingFields", "medium", len(data_metrics["missingFields"]))
        section += (
            f"\n**{priority} - Missing Data Fields** ({len(data_metrics['missingFields'])} found)\n"
        )
        for field in data_metrics["missingFields"][:3]:
            section += f"- {field}\n"
        if len(data_metrics["missingFields"]) > 3:
            section += f"- ... and {len(data_metrics['missingFields']) - 3} more\n"

    if data_metrics.get("staleTimestamps"):
        priority = get_priority_tag(
            "staleTimestamps", "medium", len(data_metrics["staleTimestamps"])
        )
        section += (
            f"\n**{priority} - Stale Timestamps** ({len(data_metrics['staleTimestamps'])} found)\n"
        )
        for timestamp in data_metrics["staleTimestamps"][:3]:
            section += f"- {timestamp}\n"

    # Layout Issues
    if layout_issues.get("overflowElements"):
        priority = get_priority_tag(
            "overflowElements", "critical", len(layout_issues["overflowElements"])
        )
        section += f"\n**{priority} - Layout Overflow** ({len(layout_issues['overflowElements'])} elements)\n"
        for element in layout_issues["overflowElements"][:3]:
            section += f"- {element}\n"

    if layout_issues.get("responsiveIssues"):
        priority = get_priority_tag(
            "responsiveIssues", "medium", len(layout_issues["responsiveIssues"])
        )
        section += f"\n**{priority} - Responsive Issues** ({len(layout_issues['responsiveIssues'])} found)\n"
        for issue in layout_issues["responsiveIssues"][:3]:
            section += f"- {issue}\n"

    # Console Errors
    if console_errors:
        priority = get_priority_tag("consoleErrors", "critical", len(console_errors))
        section += f"\n**{priority} - Console Errors** ({len(console_errors)} found)\n"
        for error in console_errors[:3]:
            section += f"- {error}\n"
        if len(console_errors) > 3:
            section += f"- ... and {len(console_errors) - 3} more\n"

    # Actionable Fixes
    section += "\n### 🔧 Actionable Fixes\n"

    if data_metrics.get("nanValues"):
        section += "- **Fix NaN Values:** Add null checks and fallback values in data processing\n"
        section += "- **Validation:** Implement client-side data validation before rendering\n"

    if data_metrics.get("missingFields"):
        section += "- **Empty States:** Add loading skeletons and empty state components\n"
        section += "- **Data Fallbacks:** Implement graceful degradation for missing API data\n"

    if data_metrics.get("staleTimestamps"):
        section += "- **Real-time Updates:** Implement automatic data refresh for stale content\n"
        section += "- **TTL Indicators:** Add visual indicators for data freshness\n"

    if layout_issues.get("overflowElements"):
        section += "- **Responsive Design:** Fix horizontal overflow with proper CSS constraints\n"
        section += "- **Content Truncation:** Implement text truncation for long content\n"

    if layout_issues.get("responsiveIssues"):
        section += "- **Touch Targets:** Increase button/link sizes for mobile (min 44px)\n"
        section += "- **Mobile Layout:** Improve responsive breakpoints and layouts\n"

    if console_errors:
        section += "- **Error Handling:** Fix JavaScript errors and add proper error boundaries\n"
        section += "- **Debugging:** Add error tracking and monitoring for production\n"

    if lighthouse_data and lighthouse_data.get("scores", {}).get("performance", 100) < 70:
        section += "- **Performance:** Optimize bundle size, lazy loading, and image compression\n"
        section += "- **Caching:** Implement better caching strategies for API calls\n"

    return section


def generate_summary_section(
    playwright_data: dict[str, Any], lighthouse_data: dict[str, Any] | None = None
) -> str:
    """Generate executive summary section."""
    tabs = playwright_data.get("tabs", [])
    total_tabs = len(tabs)

    # Calculate overall statistics
    total_issues = sum(
        len(tab.get("dataMetrics", {}).get("missingFields", []))
        + len(tab.get("dataMetrics", {}).get("nanValues", []))
        + len(tab.get("dataMetrics", {}).get("staleTimestamps", []))
        + len(tab.get("layoutIssues", {}).get("overflowElements", []))
        + len(tab.get("layoutIssues", {}).get("responsiveIssues", []))
        + len(tab.get("consoleErrors", []))
        for tab in tabs
    )

    critical_issues = sum(
        len(tab.get("dataMetrics", {}).get("nanValues", []))
        + len(tab.get("layoutIssues", {}).get("overflowElements", []))
        for tab in tabs
    )

    healthy_tabs = sum(
        1
        for tab in tabs
        if (
            len(tab.get("dataMetrics", {}).get("nanValues", [])) == 0
            and len(tab.get("layoutIssues", {}).get("overflowElements", [])) == 0
            and len(tab.get("consoleErrors", [])) < 2
        )
    )

    summary = f"""# 🎯 ZiggyAI UI Improvements Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Environment:** {playwright_data.get('environment', {}).get('frontendUrl', 'http://localhost:3000')}

## 📊 Executive Summary

- **Total Tabs Audited:** {total_tabs}
- **Healthy Tabs:** {healthy_tabs}/{total_tabs} ({healthy_tabs/total_tabs*100:.0f}%)
- **Total Issues:** {total_issues}
- **Critical Issues (P0):** {critical_issues}
- **Status:** {'🟢 Good' if critical_issues == 0 and total_issues < 20 else '🟡 Needs Attention' if critical_issues < 3 else '🔴 Critical Issues'}

"""

    if lighthouse_data:
        lighthouse_summary = lighthouse_data.get("summary", {})
        summary += f"""## 🚀 Performance Overview

- **Average Performance:** {format_lighthouse_score(lighthouse_summary.get('averagePerformance', 0))}
- **Average Accessibility:** {format_lighthouse_score(lighthouse_summary.get('averageAccessibility', 0))}
- **Average Best Practices:** {format_lighthouse_score(lighthouse_summary.get('averageBestPractices', 0))}
- **Average SEO:** {format_lighthouse_score(lighthouse_summary.get('averageSeo', 0))}

"""

    # Priority recommendations
    summary += """## 🎯 Priority Recommendations

### P0 - Critical (Fix Immediately)
"""

    if critical_issues > 0:
        summary += f"- **{critical_issues} critical issues** found across tabs\n"
        summary += "- Fix NaN/undefined values breaking data display\n"
        summary += "- Resolve layout overflow causing horizontal scrolling\n"
        summary += "- Address JavaScript errors breaking functionality\n"
    else:
        summary += "✅ No critical issues found!\n"

    summary += """
### P1 - High Priority (Fix This Week)
- Implement loading states and empty state components
- Add real-time data refresh for stale timestamps
- Improve error handling and user feedback
- Optimize mobile responsive design

### P2 - Medium Priority (Fix This Month)
- Performance optimization and bundle size reduction
- Enhanced accessibility compliance
- SEO improvements and meta tag optimization
- UI polish and visual consistency

"""

    return summary


def main():
    """Main function to generate UI improvements report."""
    print("🎯 Generating ZiggyAI UI Improvements Report...")

    # Load audit data
    playwright_file = "artifacts/ui/ui_audit.json"
    lighthouse_file = "artifacts/ui/lighthouse_summary.json"

    playwright_data = load_json_file(playwright_file)
    lighthouse_data = load_json_file(lighthouse_file)

    if not playwright_data:
        print(f"❌ Could not load Playwright data from {playwright_file}")
        print("💡 Run: pnpm playwright test scripts/ui_audit.spec.ts")
        sys.exit(1)

    if not lighthouse_data:
        print(f"⚠️ Could not load Lighthouse data from {lighthouse_file}")
        print("💡 Run: .\\scripts\\run_lighthouse.ps1")

    # Generate report
    report_content = generate_summary_section(playwright_data, lighthouse_data)

    # Generate sections for each tab
    tabs = playwright_data.get("tabs", [])
    lighthouse_results = (
        {r["route"]: r for r in lighthouse_data.get("results", [])} if lighthouse_data else {}
    )

    for tab in tabs:
        tab_name = tab.get("tabName", "Unknown")
        lighthouse_tab_data = lighthouse_results.get(tab_name.lower(), None)
        report_content += generate_tab_section(tab, lighthouse_tab_data)

    # Add footer
    report_content += f"""
---

## 📚 Additional Resources

- **Screenshots:** All tab screenshots are saved in `artifacts/ui/`
- **Raw Data:** Detailed audit data in `artifacts/ui/ui_audit.json`
- **Lighthouse Reports:** Individual Lighthouse reports in `artifacts/ui/lh_*.json`
- **Re-run Audits:** 
  ```bash
  # Playwright audit
  pnpm playwright test scripts/ui_audit.spec.ts
  
  # Lighthouse audit  
  .\\scripts\\run_lighthouse.ps1
  
  # Generate report
  python scripts/generate_ui_report.py
  ```

**Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}**
"""

    # Save report
    output_file = "ui_improvements.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"✅ Report generated: {output_file}")
        print(f"📊 Analyzed {len(tabs)} tabs")
        if lighthouse_data:
            print(
                f"🚀 Included Lighthouse data for {len(lighthouse_data.get('results', []))} routes"
            )
        print("📁 Screenshots available in artifacts/ui/")

    except Exception as e:
        print(f"❌ Error saving report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
