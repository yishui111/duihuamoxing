# RAG 知识库功能测试（原生版：Ollama + Open WebUI 8089）
# 用法: powershell -ExecutionPolicy Bypass -File .\tests\test_rag_chat.ps1
# 环境变量（可选）:
#   OWUI_EMAIL / OWUI_PASSWORD   Open WebUI 登录账号；提供后才测试「登录+界面对话」
# 输出 "结果: PASS" 即功能正常；日志写入 .\tests\output\
# 注意: 本文件为 UTF-8 带 BOM（Windows PowerShell 5.1 需要）

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$outDir = Join-Path $PSScriptRoot 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$log = Join-Path $outDir ("test_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))
$results = @()
$script:jwt = $null

function Write-Log($msg) { $msg | Tee-Object -FilePath $script:log -Append }

Write-Log "==== RAG 知识库测试 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===="

# 1. Ollama 模型列表（对话 qwen2.5:7b + 嵌入 bge-m3）
try {
    $tags = Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5
    $models = $tags.models | ForEach-Object { $_.name }
    Write-Log "[1/6] Ollama 模型: $($models -join ', ')"
    if ($models -contains 'qwen2.5:7b' -and ($models -contains 'bge-m3' -or $models -contains 'bge-m3:latest')) {
        Write-Log '       PASS'
        $results += 'Models'
    } else {
        Write-Log '       WARN - 缺少 qwen2.5:7b 或 bge-m3'
        $results += 'Models-WARN'
    }
} catch {
    Write-Log "[1/6] Ollama: FAIL - $_"
    $results += 'Models-FAIL'
}

# 2. RAG 嵌入测试（bge-m3）
try {
    $body = @{ model = 'bge-m3'; input = '测试嵌入向量' } | ConvertTo-Json
    $emb = Invoke-RestMethod -Uri 'http://localhost:11434/api/embed' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
    if ($emb.embeddings -and $emb.embeddings[0].Count -gt 0) {
        Write-Log "[2/6] 嵌入测试: OK (维度 $($emb.embeddings[0].Count))"
        $results += 'Embed'
    } else {
        Write-Log '[2/6] 嵌入测试: WARN - 返回为空'
        $results += 'Embed-WARN'
    }
} catch {
    Write-Log "[2/6] 嵌入测试: FAIL - $_"
    $results += 'Embed-FAIL'
}

# 3. 对话生成（Ollama 直连 qwen2.5:7b）
try {
    $body = @{ model = 'qwen2.5:7b'; messages = @(@{ role = 'user'; content = '请只回复两个字：收到' }); stream = $false } | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Uri 'http://localhost:11434/api/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
    $reply = $resp.message.content
    if ($reply) {
        Write-Log "[3/6] Ollama 对话: OK (回复: $reply)"
        $results += 'Chat'
    } else {
        Write-Log '[3/6] Ollama 对话: WARN - 回复为空'
        $results += 'Chat-WARN'
    }
} catch {
    Write-Log "[3/6] Ollama 对话: FAIL - $_"
    $results += 'Chat-FAIL'
}

# 4. Open WebUI 健康（8089）
try {
    $h = Invoke-RestMethod -Uri 'http://localhost:8089/health' -TimeoutSec 5
    Write-Log "[4/6] Open WebUI /health: OK ($($h.status))"
    $results += 'WebUI'
} catch {
    Write-Log "[4/6] Open WebUI /health: FAIL - $_"
    $results += 'WebUI-FAIL'
}

# 5. 登录认证 + 经 Open WebUI 对话（需要 OWUI_EMAIL / OWUI_PASSWORD）
$email = $env:OWUI_EMAIL
$pw = $env:OWUI_PASSWORD
if ($email -and $pw) {
    try {
        $authBody = @{ email = $email }
        $authBody['password'] = $pw
        $body = $authBody | ConvertTo-Json
        $auth = Invoke-RestMethod -Uri 'http://localhost:8089/api/v1/auths/signin' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 10
        if ($auth.token) {
            Write-Log "[5/6] 登录认证: OK (user=$($auth.email) role=$($auth.role))"
            $results += 'Auth'
            $script:jwt = $auth.token
        } else {
            Write-Log '[5/6] 登录认证: FAIL - 未返回 token'
            $results += 'Auth-FAIL'
        }
    } catch {
        Write-Log "[5/6] 登录认证: FAIL - $_"
        $results += 'Auth-FAIL'
    }
    if ($script:jwt) {
        try {
            $headers = @{ Authorization = "Bearer $($script:jwt)" }
            $body = @{ model = 'qwen2.5:7b'; messages = @(@{ role = 'user'; content = '请只回复两个字：收到' }) } | ConvertTo-Json -Depth 5
            $resp = Invoke-WebRequest -Uri 'http://localhost:8089/api/chat/completions' -Method Post -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 120 -UseBasicParsing
            $chat = [System.Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray()) | ConvertFrom-Json
            $reply = $chat.choices[0].message.content
            if ($reply) {
                Write-Log "[5/6] WebUI 对话生成: OK (回复: $reply)"
                $results += 'WebUI-Chat'
            } else {
                Write-Log '[5/6] WebUI 对话生成: WARN - 回复为空'
                $results += 'WebUI-Chat-WARN'
            }
        } catch {
            Write-Log "[5/6] WebUI 对话生成: FAIL - $_"
            $results += 'WebUI-Chat-FAIL'
        }
    }
} else {
    Write-Log '[5/6] 登录/界面对话: SKIP（未设置 OWUI_EMAIL / OWUI_PASSWORD）'
    $results += 'Auth-SKIP'
}

# 6. 语音输入接口（Whisper STT 端点存在性：应返回 400/415 而非 404）
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8089/api/v1/audio/transcriptions' -Method Post -ContentType 'multipart/form-data' -Body 'x' -TimeoutSec 10 -UseBasicParsing
    Write-Log "[6/6] 语音接口: OK (HTTP $($r.StatusCode))"
    $results += 'STT'
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -eq 400 -or $code -eq 415 -or $code -eq 422) {
        Write-Log "[6/6] 语音接口: OK (端点存在, HTTP $code)"
        $results += 'STT'
    } else {
        Write-Log "[6/6] 语音接口: FAIL - HTTP $code"
        $results += 'STT-FAIL'
    }
}

$failed = @($results | Where-Object { $_ -like '*-FAIL' })
Write-Log ''
if ($failed.Count -eq 0) {
    Write-Log '结果: PASS'
} else {
    Write-Log "结果: FAIL（$($failed.Count) 项失败）"
}
Write-Log "日志: $log"
