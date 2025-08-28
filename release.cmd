@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Usage: release.cmd 1.3.1 [--skip-build]
if "%~1"=="" (
  echo Usage: %~nx0 VERSION [--skip-build]
  echo Example: %~nx0 1.3.1
  exit /b 1
)

set VER=%~1
REM Normalize version: strip leading 'v' if provided (accept both 1.3.1 or v1.3.1)
set CLEAN_VER=%VER%
if /I "%CLEAN_VER:~0,1%"=="v" set CLEAN_VER=%CLEAN_VER:~1%
set SKIP_BUILD=0
if /I "%~2"=="--skip-build" set SKIP_BUILD=1

REM Quick sanity checks
where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git is not installed or not in PATH.
  exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not installed or not in PATH.
  exit /b 1
)
if %SKIP_BUILD%==0 (
  where scons >nul 2>&1
  if errorlevel 1 (
    echo ERROR: scons not found. Install it or rerun with --skip-build.
    exit /b 1
  )
)

REM Detect accidental double 'v' like 'vv1.3.1'
if /I "%VER:~0,2%"=="vv" (
  echo ERROR: Version appears to start with 'vv' (^%VER^). Use either '1.3.1' or 'v1.3.1'.
  exit /b 1
)

REM Validate version format using Python (digits and dots only)
python -c "import re,sys; sys.exit(0) if re.match(r'^\d+(\.\d+){0,3}$', sys.argv[1]) else sys.exit(1)" %CLEAN_VER%
if errorlevel 1 (
  echo ERROR: Invalid version format '%CLEAN_VER%'. Expected like 1.3 or 1.3.1
  exit /b 1
)

set TAG=v%CLEAN_VER%

REM Check if CI workflow exists to upload asset automatically
if not exist ".github\workflows\release.yml" (
  echo WARNING: .github\workflows\release.yml not found. GitHub won^'t auto-upload the asset.
)

REM Check if tag already exists locally or on origin
git rev-parse -q --verify refs/tags/%TAG% >nul 2>&1
if not errorlevel 1 (
  echo ERROR: Tag %TAG% already exists locally. Choose a new version or delete the tag first.
  exit /b 1
)
set FOUND_TAG=
for /f "delims=" %%i in ('git ls-remote --tags origin %TAG%') do set FOUND_TAG=1
if defined FOUND_TAG (
  echo ERROR: Tag %TAG% already exists on origin. Choose a new version.
  exit /b 1
)

echo === Step 1/5: Bump version in buildVars.py to %CLEAN_VER% ===
python -c "import sys, re, pathlib; p=pathlib.Path('buildVars.py'); t=p.read_text(encoding='utf-8'); t=re.sub(r'(\"addon_version\"\s*:\s*\")(.*?)(\")', rf'\1{sys.argv[1]}\3', t); p.write_text(t, encoding='utf-8')" %CLEAN_VER%
if errorlevel 1 (
  echo Failed to bump version. Ensure Python is installed and accessible.
  exit /b 1
)

echo === Step 2/5: Commit version bump ===
git add buildVars.py
git commit -m "Bump version to %VER%" >nul 2>&1
if errorlevel 1 (
  echo No changes to commit or git commit failed. Continuing...
)

echo === Step 3/5: Optional local build (sanity check) ===
if %SKIP_BUILD%==0 (
  scons -Q
  if errorlevel 1 (
    echo Build failed. Fix errors before releasing.
    exit /b 1
  )
  if not exist "spellcheck-%CLEAN_VER%.nvda-addon" (
    echo Expected artifact spellcheck-%CLEAN_VER%.nvda-addon not found. Verify addon_version and try again.
    exit /b 1
  )
)

echo === Step 4/5: Push main ===
git push origin main
if errorlevel 1 (
  echo Git push failed.
  exit /b 1
)

echo === Step 5/5: Tag and push to trigger GitHub Actions release ===
git tag v%CLEAN_VER%
if errorlevel 1 (
  echo Failed to create tag. It may already exist.
)
git push origin v%CLEAN_VER%
if errorlevel 1 (
  echo Failed to push tag. Ensure the tag is unique and you have permissions.
  exit /b 1
)

echo Done. Check the Actions tab for the build and the Releases page for v%CLEAN_VER%.
echo If CI is enabled, the download URL will be:
echo   https://github.com/OWNER/REPO/releases/download/v%CLEAN_VER%/spellcheck-%CLEAN_VER%.nvda-addon
echo Replace OWNER/REPO with your GitHub repo (e.g., hmdqr/spellcheck).
exit /b 0
