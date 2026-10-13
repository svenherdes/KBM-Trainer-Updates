# KBM-Trainer 1.4.3: git-data API, atomic publication of approved source files.
# Local training data, .env, DB files, installers, secrets and build outputs are excluded.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$repository = 'svenherdes/KBM-Trainer-Updates'
$branch = 'main'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manifestPath = Join-Path $root 'SOURCE_AUDIT_SHA256.json'

function Assert($condition, $message) {
    if (-not $condition) { throw $message }
}

try {
    Write-Host 'Der Quellcode wird unter GPL-3.0-only dauerhaft oeffentlich zugaenglich.'
    Write-Host 'Trainingsprofile, lokale Datenbanken, Installer und version.json werden NICHT hochgeladen.'
    $consent = Read-Host 'Oeffentliche Veroeffentlichung jetzt starten? (J/N)'
    if ($consent -notin @('J','j')) { Write-Host 'Abgebrochen, nichts hochgeladen.'; exit 0 }

    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        foreach ($path in @("$env:ProgramFiles\GitHub CLI\gh.exe", "${env:ProgramFiles(x86)}\GitHub CLI\gh.exe", "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe")) {
            if (Test-Path $path) { $gh = Get-Item $path; break }
        }
    }
    Assert $gh 'GitHub CLI (gh) nicht gefunden. Bitte zuerst GitHub CLI installieren.'
    $ghExe = $gh.Source
    if (-not $ghExe) { $ghExe = $gh.FullName }
    $tokenLines = @(& $ghExe auth token 2>$null)
    Assert ($LASTEXITCODE -eq 0 -and $tokenLines.Count -gt 0) 'GitHub CLI nicht angemeldet. Bitte gh auth login ausfuehren.'
    $token = [string]$tokenLines[0]
    Assert ($token.Length -gt 20) 'GitHub-Anmeldung unvollstaendig.'

    $headers = @{
        Authorization='Bearer ' + $token
        Accept='application/vnd.github+json'
        'User-Agent'='KBM-Trainer-OpenSource-Publisher'
        'X-GitHub-Api-Version'='2022-11-28'
    }
    function GithubApi($method, $path, $body = $null) {
        $opts = @{
            Uri=('https://api.github.com/repos/' + $repository + '/' + $path)
            Method=$method
            Headers=$headers
            TimeoutSec=120
        }
        if ($null -ne $body) {
            $payload = ConvertTo-Json -InputObject $body -Depth 15 -Compress
            $opts['ContentType'] = 'application/json; charset=utf-8'
            $opts['Body'] = [Text.Encoding]::UTF8.GetBytes($payload)
        }
        return Invoke-RestMethod @opts
    }

    Write-Host 'Pruefe bestehendes GitHub-Update ...'
    $existingVersionFile = GithubApi 'Get' ('contents/version.json?ref=' + $branch)
    $existingVersion = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($existingVersionFile.content -replace '\s',''))) | ConvertFrom-Json
    Assert ($existingVersion.version -eq '1.4.3') 'GitHub ist nicht auf 1.4.3. Ohne Pruefung wird nichts geaendert.'
    Assert ($existingVersion.channel -eq 'stable') 'GitHub Versionskanal unerwartet. Abbruch.'

    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
    $paths = @($manifest.PSObject.Properties.Name | Sort-Object)
    Assert ($paths.Count -ge 30) 'Zu wenige Quelldateien im Pruefprotokoll.'
    foreach ($rel in $paths) {
        Assert ($rel -notmatch '(^/|^\.\.|/\.\./|\\|:|\x00)') ('Ungueltiger Dateipfad: ' + $rel)
        $file = Join-Path $root ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
        Assert (Test-Path -LiteralPath $file -PathType Leaf) ('Datei fehlt: ' + $rel)
        $expected = [string]($manifest.PSObject.Properties[$rel].Value)
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant()
        Assert ($actual -eq $expected) ('Datei veraendert, Abbruch: ' + $rel)
    }

    Write-Host ('Pruefung bestanden: ' + $paths.Count + ' Dateien, keine Nutzerdaten im Upload.')
    Write-Host 'Erstelle GitHub-Quellcode-Commit (ohne den bestehenden Release zu aendern) ...'
    $oldRef = GithubApi 'Get' ('git/ref/heads/' + $branch)
    $headSha = [string]$oldRef.object.sha
    $oldCommit = GithubApi 'Get' ('git/commits/' + $headSha)
    $baseTreeSha = [string]$oldCommit.tree.sha
    $entries = @()
    $n = 0
    foreach ($rel in $paths) {
        $file = Join-Path $root ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
        $base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($file))
        $blob = GithubApi 'Post' 'git/blobs' @{content=$base64; encoding='base64'}
        $entries += @{path=$rel;mode='100644';type='blob';sha=[string]$blob.sha}
        $n++
        Write-Host ("  $n/$($paths.Count): $rel")
    }
    # Source audit manifest itself is included, but its own digest is excluded to avoid recursion.
    $auditBlob = GithubApi 'Post' 'git/blobs' @{content=[Convert]::ToBase64String([IO.File]::ReadAllBytes($manifestPath));encoding='base64'}
    $entries += @{path='SOURCE_AUDIT_SHA256.json'; mode='100644';type='blob';sha=[string]$auditBlob.sha}

    $tree = GithubApi 'Post' 'git/trees' @{base_tree=$baseTreeSha;tree=@($entries)}
    $commit = GithubApi 'Post' 'git/commits' @{
        message='Publish KBM-Trainer 1.4.3 source under GPL-3.0-only'
        tree=[string]$tree.sha
        parents=@($headSha)
    }
    # Fast-forward only: refuse concurrent edits, never force push.
    $result = GithubApi 'Patch' ('git/refs/heads/' + $branch) @{sha=[string]$commit.sha;force=$false}
    Assert ([string]$result.object.sha -eq [string]$commit.sha) 'GitHub-Commit konnte nicht verifiziert werden.'
    $remoteVersionFile = GithubApi 'Get' ('contents/version.json?ref=' + $branch)
    Assert ($remoteVersionFile.sha -eq $existingVersionFile.sha) 'Achtung: version.json hat sich geaendert! Bitte melden.'

    Write-Host ''
    Write-Host 'ERFOLG: Quellcode unter GPL-3.0-only auf GitHub.'
    Write-Host ('Commit: https://github.com/' + $repository + '/commit/' + $commit.sha)
    Write-Host 'Release v1.4.3 und Updatehinweis wurden NICHT veraendert.'
    exit 0
}
catch {
    Write-Host ''
    Write-Host ('FEHLER: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Kein Windows-Programm wurde geaendert. Bei Fehler vor dem finalen Commit ist GitHub unveraendert.'
    exit 1
}
