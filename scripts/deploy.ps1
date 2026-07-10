# RailYatra Deployment & Launch Automation Script
# Exit Code 0 = Successful Deploy, 1 = Failed Deploy & Rolled Back

$ErrorActionPreference = "Stop"

Write-Output "====================================================================="
Write-Output "STARTING RAILYATRA PRODUCTION DEPLOYMENT & GO-LIVE PIPELINE"
Write-Output "====================================================================="

# Step 1: Pre-deployment checks
Write-Output "[1/5] Running pre-deployment environment validation..."
if (!(Test-Path "apps/backend/.env") -and $env:DATABASE_URL -eq $null) {
    Write-Error "CRITICAL: Missing apps/backend/.env or DATABASE_URL environment variable."
}

# Step 2: Database Migration
Write-Output "[2/5] Running database migrations..."
try {
    cd apps/backend
    npx prisma db push --accept-data-loss
    cd ../..
    Write-Output "Database schema push completed successfully."
} catch {
    Write-Error "CRITICAL: Database migration failed. Aborting deploy."
    exit 1
}

# Step 3: Application Process Startup
Write-Output "[3/5] Starting application services under PM2..."
try {
    # Stop existing processes to avoid locked file issues
    pm2 stop ecosystem.config.js 2>$null | Out-Null
    
    # Start fresh
    pm2 start ecosystem.config.js
    
    # Sleep to allow services to start and bind to ports
    Write-Output "Waiting 10 seconds for services to initialize..."
    Start-Sleep -Seconds 10
    
    pm2 status
} catch {
    Write-Error "CRITICAL: PM2 startup failed. Aborting deploy."
    exit 1
}

# Step 4: Verification & Smoke Testing
Write-Output "[4/5] Running production smoke test suite..."
$smokePassed = $false
try {
    # Set execution policy to run local script if needed
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    
    # Run the smoke test suite
    powershell -File ./scripts/smoke-test.ps1
    $smokePassed = $true
} catch {
    $smokePassed = $false
    Write-Output "SMOKE TESTS ENCOUNTERED RUNTIME EXCEPTION: $_"
}

# Step 5: Rollback decision
if ($smokePassed) {
    Write-Output "[5/5] Deployment completed successfully! All gates passed."
    Write-Output "====================================================================="
    exit 0
} else {
    Write-Output "====================================================================="
    Write-Warning "SMOKE TESTS FAILED! INITIATING AUTOMATED ROLLBACK PLAYBOOK..."
    Write-Output "====================================================================="
    
    try {
        Write-Output "Stopping current buggy deployments..."
        pm2 stop ecosystem.config.js
        
        Write-Output "Reverting git commit to previous stable release..."
        git reset --hard HEAD~1
        
        Write-Output "Re-building previous stable backend..."
        cd apps/backend
        npm run build
        cd ../..
        
        Write-Output "Restoring previous stable service instances..."
        pm2 start ecosystem.config.js
        
        Write-Output "====================================================================="
        Write-Warning "ROLLBACK COMPLETED. SYSTEM RESTORED TO PREVIOUS STABLE STATE."
        Write-Output "====================================================================="
        exit 1
    } catch {
        Write-Error "CRITICAL ROLLBACK FAILURE: System is in an unstable state. Manual intervention required!"
        exit 1
    }
}
