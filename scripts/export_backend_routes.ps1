#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'
$Raw  = Join-Path $Docs '_raw'
if (-not (Test-Path $Raw)) { New-Item -ItemType Directory -Path $Raw -Force | Out-Null }

$backend = Join-Path $Root 'backend'
$routesOut = Join-Path $Raw '_routes_backend.json'

if (-not (Test-Path -LiteralPath $backend)) {
    '{"routes": []}' | Out-File -LiteralPath $routesOut -Encoding UTF8
    return
}

# Detect FastAPI by files or requirements
$hasFastApi = $false
if (Test-Path (Join-Path $backend 'app\main.py')) { $hasFastApi = $true }
if (-not $hasFastApi) {
    $reqPath = Join-Path $backend 'requirements.txt'
    if (Test-Path $reqPath) {
        $hasFastApi = Select-String -Path $reqPath -Pattern '(?i)^fastapi' -SimpleMatch -Quiet
    }
}
if (-not $hasFastApi) {
    $pyproj = Join-Path $backend 'pyproject.toml'
    if (Test-Path $pyproj) {
        $hasFastApi = Select-String -Path $pyproj -Pattern '(?i)fastapi' -Quiet
    }
}

if (-not $hasFastApi) {
    '{"routes": []}' | Out-File -LiteralPath $routesOut -Encoding UTF8
    return
}

# Ensure helper exists
$toolsDir = Join-Path $backend 'tools'
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null }
$helper = Join-Path $toolsDir 'export_routes.py'

# Write (or overwrite) helper idempotently
@'
#!/usr/bin/env python
import json, os, sys, importlib, traceback

def find_app_instance(mod):
    try:
        from fastapi import FastAPI
    except Exception:
        return None
    # common name
    app = getattr(mod, 'app', None)
    if app is not None and isinstance(app, FastAPI):
        return app
    # search attributes
    for name in dir(mod):
        obj = getattr(mod, name)
        try:
            if isinstance(obj, FastAPI):
                return obj
        except Exception:
            continue
    return None

def route_entry(r):
    try:
        methods = sorted([m for m in r.methods if m not in ('HEAD','OPTIONS')])
    except Exception:
        methods = []
    path = getattr(r, 'path', getattr(r, 'path_format', None))
    name = getattr(r, 'name', None)
    endpoint = getattr(r, 'endpoint', None)
    fn_file = None
    fn_line = None
    handler = None
    if endpoint is not None:
        try:
            code = getattr(endpoint, '__code__', None)
            if code is not None:
                fn_file = code.co_filename
                fn_line = code.co_firstlineno
            handler = getattr(endpoint, '__name__', repr(endpoint))
        except Exception:
            handler = repr(endpoint)
    return {
        'methods': methods,
        'path': path,
        'name': name,
        'handler': handler,
        'file': fn_file,
        'line': fn_line,
    }

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    repo_root = os.path.abspath(os.path.join(root, '..'))
    sys.path.insert(0, root)
    sys.path.insert(0, repo_root)
    mod_candidates = [
        ('app.main', 'app'),
        ('backend.app.main', 'app'),
    ]
    app = None
    tried = []
    for mod_name, attr in mod_candidates:
        try:
            mod = importlib.import_module(mod_name)
            app = find_app_instance(mod)
            if app is not None:
                break
        except Exception as e:
            tried.append(f"{mod_name}: {e}")
            continue
    if app is None:
        print(json.dumps({'routes': [], 'error': 'FastAPI app not found', 'tried': tried}))
        return 0
    routes = []
    try:
        for r in getattr(app, 'routes', []):
            try:
                entry = route_entry(r)
                if entry.get('path'):
                    routes.append(entry)
            except Exception:
                continue
    except Exception:
        pass
    print(json.dumps({'routes': routes}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        print(json.dumps({'routes': [], 'error': traceback.format_exc()}))
        sys.exit(0)
'@ | Out-File -LiteralPath $helper -Encoding UTF8

# Execute helper
$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    '{"routes": [], "error": "Python not available"}' | Out-File -LiteralPath $routesOut -Encoding UTF8
    return
}

try {
    & python $helper | Out-File -LiteralPath $routesOut -Encoding UTF8
} catch {
    '{"routes": []}' | Out-File -LiteralPath $routesOut -Encoding UTF8
}
