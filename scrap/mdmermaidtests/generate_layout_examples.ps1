# PowerShell script to generate layout examples with black background

$env:PUPPETEER_EXECUTABLE_PATH="C:\Users\craig\.cache\puppeteer\chrome-headless-shell\win64-142.0.7444.162\chrome-headless-shell-win64\chrome-headless-shell.exe"

Set-Location $PSScriptRoot

Write-Host "Generating layout examples with black background..." -ForegroundColor Cyan

# Generate images from markdown
mmdc -i layout_examples.md -o layout_examples_output.md -t dark -b black -a layout_images

Write-Host "`nDone! Check layout_images folder for generated diagrams." -ForegroundColor Green

