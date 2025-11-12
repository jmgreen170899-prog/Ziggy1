# ZiggyAI Lighthouse Performance and Accessibility Audit
# Runs Lighthouse against all ZiggyAI routes and saves detailed reports

param(
    [string]$FrontendUrl = "http://localhost:3000",
    [string]$OutputDir = "artifacts/ui",
    [int]$TimeoutSeconds = 60
)

Write-Host "🔍 Starting Lighthouse audit for ZiggyAI..." -ForegroundColor Cyan
Write-Host "📍 Frontend URL: $FrontendUrl" -ForegroundColor Gray
Write-Host "📁 Output Directory: $OutputDir" -ForegroundColor Gray

# Ensure output directory exists
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Define ZiggyAI routes to audit
$routes = @(
    @{ name = "dashboard"; path = "/" },
    @{ name = "chat"; path = "/chat" },
    @{ name = "market"; path = "/market" },
    @{ name = "alerts"; path = "/alerts" },
    @{ name = "portfolio"; path = "/portfolio" },
    @{ name = "trading"; path = "/trading" },
    @{ name = "predictions"; path = "/predictions" },
    @{ name = "news"; path = "/news" },
    @{ name = "paper-trading"; path = "/paper-trading" },
    @{ name = "paper-status"; path = "/paper/status" },
    @{ name = "live"; path = "/live" },
    @{ name = "crypto"; path = "/crypto" },
    @{ name = "learning"; path = "/learning" },
    @{ name = "account"; path = "/account" }
)

# Check if Lighthouse is installed
try {
    $lighthouseVersion = lighthouse --version
    Write-Host "✅ Lighthouse version: $lighthouseVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Lighthouse not found. Installing..." -ForegroundColor Red
    Write-Host "💡 Run: npm install -g lighthouse" -ForegroundColor Yellow
    exit 1
}

# Check if frontend is running
try {
    $response = Invoke-WebRequest -Uri $FrontendUrl -Method HEAD -TimeoutSec 5
    Write-Host "✅ Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend not accessible at $FrontendUrl" -ForegroundColor Red
    Write-Host "💡 Start frontend with: npm run dev" -ForegroundColor Yellow
    exit 1
}

$auditResults = @()
$totalRoutes = $routes.Count
$currentRoute = 0

foreach ($route in $routes) {
    $currentRoute++
    $url = "$FrontendUrl$($route.path)"
    $outputFile = "$OutputDir/lh_$($route.name).json"
    
    Write-Host "[$currentRoute/$totalRoutes] 🔍 Auditing: $($route.name) ($url)" -ForegroundColor Cyan
    
    try {
        # Run Lighthouse with comprehensive config
        $lighthouseArgs = @(
            $url,
            "--output=json",
            "--output-path=$outputFile",
            "--chrome-flags=--headless --no-sandbox --disable-gpu",
            "--quiet",
            "--timeout=$($TimeoutSeconds * 1000)",
            "--throttling-method=simulate",
            "--form-factor=desktop",
            "--screenEmulation.disabled",
            "--only-categories=performance,accessibility,best-practices,seo"
        )
        
        $process = Start-Process -FilePath "lighthouse" -ArgumentList $lighthouseArgs -Wait -NoNewWindow -PassThru
        
        if ($process.ExitCode -eq 0 -and (Test-Path $outputFile)) {
            # Parse Lighthouse results
            $lighthouseData = Get-Content $outputFile | ConvertFrom-Json
            
            $auditSummary = @{
                route = $route.name
                url = $url
                timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
                scores = @{
                    performance = [math]::Round($lighthouseData.categories.performance.score * 100, 1)
                    accessibility = [math]::Round($lighthouseData.categories.accessibility.score * 100, 1)
                    bestPractices = [math]::Round($lighthouseData.categories."best-practices".score * 100, 1)
                    seo = [math]::Round($lighthouseData.categories.seo.score * 100, 1)
                }
                metrics = @{
                    firstContentfulPaint = $lighthouseData.audits."first-contentful-paint".numericValue
                    largestContentfulPaint = $lighthouseData.audits."largest-contentful-paint".numericValue
                    cumulativeLayoutShift = $lighthouseData.audits."cumulative-layout-shift".numericValue
                    totalBlockingTime = $lighthouseData.audits."total-blocking-time".numericValue
                }
                issues = @{
                    performance = @()
                    accessibility = @()
                    bestPractices = @()
                    seo = @()
                }
            }
            
            # Extract failed audits
            foreach ($audit in $lighthouseData.audits.PSObject.Properties) {
                $auditData = $audit.Value
                if ($auditData.score -ne $null -and $auditData.score -lt 1) {
                    $category = switch ($auditData.group) {
                        "a11y-*" { "accessibility" }
                        "best-practices-*" { "bestPractices" }
                        "seo" { "seo" }
                        default { "performance" }
                    }
                    
                    $auditSummary.issues[$category] += @{
                        id = $audit.Name
                        title = $auditData.title
                        description = $auditData.description
                        score = $auditData.score
                    }
                }
            }
            
            $auditResults += $auditSummary
            
            Write-Host "✅ Performance: $($auditSummary.scores.performance)% | Accessibility: $($auditSummary.scores.accessibility)% | Best Practices: $($auditSummary.scores.bestPractices)% | SEO: $($auditSummary.scores.seo)%" -ForegroundColor Green
            
        } else {
            Write-Host "❌ Lighthouse audit failed for $($route.name)" -ForegroundColor Red
            $auditResults += @{
                route = $route.name
                url = $url
                timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
                error = "Lighthouse audit failed"
                scores = @{ performance = 0; accessibility = 0; bestPractices = 0; seo = 0 }
            }
        }
        
    } catch {
        Write-Host "❌ Error auditing $($route.name): $($_.Exception.Message)" -ForegroundColor Red
        $auditResults += @{
            route = $route.name
            url = $url
            timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
            error = $_.Exception.Message
            scores = @{ performance = 0; accessibility = 0; bestPractices = 0; seo = 0 }
        }
    }
    
    # Small delay between audits
    Start-Sleep -Seconds 2
}

# Save comprehensive lighthouse summary
$lighthouseSummary = @{
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    frontendUrl = $FrontendUrl
    totalRoutes = $totalRoutes
    results = $auditResults
    summary = @{
        averagePerformance = ($auditResults | Measure-Object -Property { $_.scores.performance } -Average).Average
        averageAccessibility = ($auditResults | Measure-Object -Property { $_.scores.accessibility } -Average).Average
        averageBestPractices = ($auditResults | Measure-Object -Property { $_.scores.bestPractices } -Average).Average
        averageSeo = ($auditResults | Measure-Object -Property { $_.scores.seo } -Average).Average
    }
}

$summaryPath = "$OutputDir/lighthouse_summary.json"
$lighthouseSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $summaryPath -Encoding UTF8

Write-Host "`n📊 Lighthouse Audit Complete!" -ForegroundColor Green
Write-Host "📁 Individual reports: $OutputDir/lh_*.json" -ForegroundColor Gray
Write-Host "📋 Summary report: $summaryPath" -ForegroundColor Gray
Write-Host "`n🎯 Average Scores:" -ForegroundColor Cyan
Write-Host "   Performance: $([math]::Round($lighthouseSummary.summary.averagePerformance, 1))%" -ForegroundColor $(if ($lighthouseSummary.summary.averagePerformance -ge 90) { "Green" } elseif ($lighthouseSummary.summary.averagePerformance -ge 50) { "Yellow" } else { "Red" })
Write-Host "   Accessibility: $([math]::Round($lighthouseSummary.summary.averageAccessibility, 1))%" -ForegroundColor $(if ($lighthouseSummary.summary.averageAccessibility -ge 90) { "Green" } elseif ($lighthouseSummary.summary.averageAccessibility -ge 50) { "Yellow" } else { "Red" })
Write-Host "   Best Practices: $([math]::Round($lighthouseSummary.summary.averageBestPractices, 1))%" -ForegroundColor $(if ($lighthouseSummary.summary.averageBestPractices -ge 90) { "Green" } elseif ($lighthouseSummary.summary.averageBestPractices -ge 50) { "Yellow" } else { "Red" })
Write-Host "   SEO: $([math]::Round($lighthouseSummary.summary.averageSeo, 1))%" -ForegroundColor $(if ($lighthouseSummary.summary.averageSeo -ge 90) { "Green" } elseif ($lighthouseSummary.summary.averageSeo -ge 50) { "Yellow" } else { "Red" })

exit 0