# RailYatra Minimum Production Smoke Test Suite
# Exit Code 0 = PASS, 1 = FAIL

param (
    [string]$BaseUrl = "http://localhost:5000",
    [string]$AiUrl = "http://localhost:8000"
)

$FailCount = 0

Write-Output "====================================================================="
Write-Output "STARTING RAILYATRA PRODUCTION SMOKE TEST SUITE"
Write-Output "====================================================================="

# Helper function to print test results
function Assert-Test {
    param (
        [string]$TestName,
        [boolean]$Condition,
        [string]$Details = ""
    )
    if ($Condition) {
        Write-Output " [PASS] $TestName"
    } else {
        Write-Output " [FAIL] $TestName - $Details"
        $script:FailCount++
    }
}

# Generate unique email for registration
$Random = Get-Random -Minimum 1000 -Maximum 9999
$TestEmail = "smoke_user_$Random@railyatra.com"
$TestPassword = "SuperSecurePassword123!"
$TestName = "Smoke Test User"

# 1. Health Endpoints Check (Liveness/Readiness)
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -Method GET
    Assert-Test "Backend Liveness Check" ($health.status -ne $null) "Response is empty"
} catch {
    Assert-Test "Backend Liveness Check" $false $_.Exception.Message
}

try {
    $ready = Invoke-RestMethod -Uri "$BaseUrl/api/health/ready" -Method GET
    Assert-Test "Backend Readiness Check" ($ready.status -eq "ready") "Status is not ready: $($ready.status)"
} catch {
    Assert-Test "Backend Readiness Check" $false $_.Exception.Message
}

try {
    $aiHealth = Invoke-RestMethod -Uri "$AiUrl/health" -Method GET
    Assert-Test "FastAPI Liveness Check" ($aiHealth.status -eq "healthy" -or $aiHealth.status -eq "degraded") "Status: $($aiHealth.status)"
} catch {
    Assert-Test "FastAPI Liveness Check" $false $_.Exception.Message
}

# 2. User Registration
$regBody = @{
    email = $TestEmail
    password = $TestPassword
    fullName = $TestName
} | ConvertTo-Json

$accessToken = ""
$userId = ""

try {
    $regResponse = Invoke-RestMethod -Uri "$BaseUrl/auth/register" -Method POST -Body $regBody -ContentType "application/json"
    Assert-Test "User Registration Endpoint" ($regResponse.success -eq $true) "Registration failed"
    if ($regResponse.success) {
        $userId = $regResponse.data.id
    }
} catch {
    Assert-Test "User Registration Endpoint" $false $_.Exception.Message
}

# 3. User Login
$loginBody = @{
    email = $TestEmail
    password = $TestPassword
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BaseUrl/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    Assert-Test "User Login Endpoint" ($loginResponse.success -eq $true -and $loginResponse.data.accessToken -ne $null) "Login failed"
    if ($loginResponse.success) {
        $accessToken = $loginResponse.data.accessToken
    }
} catch {
    Assert-Test "User Login Endpoint" $false $_.Exception.Message
}

# Check if we got token before continuing auth-protected tests
if ($accessToken -eq "") {
    Write-Output "Critical: Access token is missing, skipping auth-dependent tests."
    $script:FailCount++
} else {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }

    # 4. Auth-Protected Me Route
    try {
        $meResponse = Invoke-RestMethod -Uri "$BaseUrl/auth/me" -Method GET -Headers $headers
        Assert-Test "Profile Recovery Check (Me Endpoint)" ($meResponse.success -eq $true -and $meResponse.data.email -eq $TestEmail) "Profile mismatch"
    } catch {
        Assert-Test "Profile Recovery Check" $false $_.Exception.Message
    }

    # 5. Create Conversation
    $convId = ""
    $convBody = @{
        summary = "Smoke Test Conversation"
    } | ConvertTo-Json

    try {
        $convResponse = Invoke-RestMethod -Uri "$BaseUrl/api/conversations" -Method POST -Headers $headers -Body $convBody
        Assert-Test "Create Conversation Endpoint" ($convResponse.id -ne $null) "Failed to create conversation"
        if ($convResponse.id) {
            $convId = $convResponse.id
        }
    } catch {
        Assert-Test "Create Conversation Endpoint" $false $_.Exception.Message
    }

    # 6. Stream Chat Response
    if ($convId -ne "") {
        try {
            $chatBody = @{
                message = "I want to search a train from NDLS to BGP"
            } | ConvertTo-Json
            
            # Hit chat endpoint to initiate streaming proxy
            $chatResponse = Invoke-WebRequest -Uri "$BaseUrl/api/conversations/$convId/chat" -Method POST -Headers $headers -Body $chatBody -TimeoutSec 15
            Assert-Test "AI Chat Stream Proxy Endpoint" ($chatResponse.StatusCode -eq 200) "Chat streaming failed with status $($chatResponse.StatusCode)"
        } catch {
            Assert-Test "AI Chat Stream Proxy Endpoint" $false $_.Exception.Message
        }

        # 7. Delete Conversation
        try {
            $deleteResponse = Invoke-RestMethod -Uri "$BaseUrl/api/conversations/$convId" -Method DELETE -Headers $headers
            Assert-Test "Delete Conversation Endpoint" ($deleteResponse.success -eq $true) "Failed to delete conversation"
        } catch {
            Assert-Test "Delete Conversation Endpoint" $false $_.Exception.Message
        }

        # 7.1 Notifications Retrieval Check
        try {
            $notifResponse = Invoke-RestMethod -Uri "$BaseUrl/api/engagement/notifications" -Method GET -Headers $headers
            Assert-Test "Notifications Retrieval Endpoint" ($notifResponse -ne $null) "Response is null"
        } catch {
            Assert-Test "Notifications Retrieval Endpoint" $false $_.Exception.Message
        }
    }
}

# 8. JWT Refresh Failure Rejection Check
try {
    $refreshResponse = Invoke-RestMethod -Uri "$BaseUrl/auth/refresh" -Method POST
    Assert-Test "JWT Refresh Failure Rejection" $false "Expected unauthorized, but got success"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Assert-Test "JWT Refresh Failure Rejection" ($statusCode -eq 401 -or $statusCode -eq 400) "Status: $statusCode"
}

# 9. Invalid JWT Rejection Check
try {
    $badHeaders = @{ "Authorization" = "Bearer invalid_token_here" }
    $badMe = Invoke-RestMethod -Uri "$BaseUrl/auth/me" -Method GET -Headers $badHeaders
    Assert-Test "Invalid JWT Rejection" $false "Expected unauthorized, but got success"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Assert-Test "Invalid JWT Rejection" ($statusCode -eq 401) "Status: $statusCode"
}

# 10. Unauthorized Endpoints Rejection Check
try {
    $anonMe = Invoke-RestMethod -Uri "$BaseUrl/auth/me" -Method GET
    Assert-Test "Unauthorized Endpoint Rejection" $false "Expected unauthorized, but got success"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Assert-Test "Unauthorized Endpoint Rejection" ($statusCode -eq 401) "Status: $statusCode"
}

# 11. Journey Intelligence core engine test (FastAPI direct mock call)
try {
    $intelBody = @{
        source = "NDLS"
        destination = "BGP"
        journey_date = "2026-07-28"
        preferred_class = "3A"
    } | ConvertTo-Json
    $intelResponse = Invoke-RestMethod -Uri "$AiUrl/api/intelligence/analyze" -Method POST -Body $intelBody -ContentType "application/json"
    Assert-Test "FastAPI Journey Intelligence Endpoint" ($intelResponse.recommendations -ne $null -or $intelResponse.options -ne $null) "Journey analysis failed"
} catch {
    Assert-Test "FastAPI Journey Intelligence Endpoint" $false $_.Exception.Message
}

# 12. User Logout Endpoint Check
try {
    $logoutResponse = Invoke-RestMethod -Uri "$BaseUrl/auth/logout" -Method POST
    Assert-Test "User Logout Endpoint" ($logoutResponse.success -eq $true) "Logout failed"
} catch {
    Assert-Test "User Logout Endpoint" $false $_.Exception.Message
}

# Clean up test user directly in database if possible or log completion
Write-Output "Smoke test cleanup: temporary user $TestEmail successfully created."

Write-Output "====================================================================="
if ($FailCount -eq 0) {
    Write-Output "SUCCESS: ALL SMOKE TESTS PASSED"
    exit 0
} else {
    Write-Output "FAILURE: $FailCount SMOKE TESTS FAILED"
    exit 1
}
