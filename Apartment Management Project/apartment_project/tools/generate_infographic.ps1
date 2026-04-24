$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

function Get-ContentUtf8 {
    param([string]$Path)
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function New-Color {
    param(
        [int]$R,
        [int]$G,
        [int]$B,
        [int]$A = 255
    )
    return [System.Drawing.Color]::FromArgb($A, $R, $G, $B)
}

function New-FontSafe {
    param(
        [string[]]$Names,
        [float]$Size,
        [System.Drawing.FontStyle]$Style = [System.Drawing.FontStyle]::Regular
    )

    foreach ($name in $Names) {
        try {
            return New-Object System.Drawing.Font($name, $Size, $Style)
        } catch {
        }
    }

    return New-Object System.Drawing.Font('Segoe UI', $Size, $Style)
}

function New-RoundedRectPath {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $diameter = $Radius * 2
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function Fill-RoundedRect {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Brush]$Brush,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = New-RoundedRectPath -X $X -Y $Y -Width $Width -Height $Height -Radius $Radius
    $Graphics.FillPath($Brush, $path)
    $path.Dispose()
}

function Draw-RoundedRectBorder {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Pen]$Pen,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = New-RoundedRectPath -X $X -Y $Y -Width $Width -Height $Height -Radius $Radius
    $Graphics.DrawPath($Pen, $path)
    $path.Dispose()
}

function Draw-WrappedText {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [System.Drawing.Font]$Font,
        [System.Drawing.Brush]$Brush,
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$LineHeight,
        [int]$MaxLines = 0
    )

    $words = $Text -split '\s+'
    $lines = New-Object System.Collections.Generic.List[string]
    $current = ''

    foreach ($word in $words) {
        if ([string]::IsNullOrWhiteSpace($current)) {
            $test = $word
        } else {
            $test = "$current $word"
        }

        $size = $Graphics.MeasureString($test, $Font)
        if ($size.Width -le $Width -or [string]::IsNullOrWhiteSpace($current)) {
            $current = $test
        } else {
            $lines.Add($current)
            $current = $word
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($current)) {
        $lines.Add($current)
    }

    if ($MaxLines -gt 0 -and $lines.Count -gt $MaxLines) {
        $trimmed = New-Object System.Collections.Generic.List[string]
        for ($i = 0; $i -lt $MaxLines; $i++) {
            $trimmed.Add($lines[$i])
        }
        $lastIndex = $trimmed.Count - 1
        $trimmed[$lastIndex] = $trimmed[$lastIndex].TrimEnd() + '...'
        $lines = $trimmed
    }

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $Graphics.DrawString($lines[$i], $Font, $Brush, $X, $Y + ($i * $LineHeight))
    }

    return $lines.Count
}

function Draw-SectionTitle {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [float]$X,
        [float]$Y,
        [System.Drawing.Font]$Font,
        [System.Drawing.Brush]$Brush,
        [System.Drawing.Pen]$AccentPen
    )

    $Graphics.DrawLine($AccentPen, $X, $Y + 18, $X + 70, $Y + 18)
    $Graphics.DrawString($Text, $Font, $Brush, $X + 95, $Y)
}

$root = Split-Path -Parent $PSScriptRoot
$contentPath = Join-Path $PSScriptRoot 'infographic_content.json'
$outputDir = Join-Path $root 'output'
$outputPath = Join-Path $outputDir 'apartment-management-infographic-60x160-formal.png'

if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$data = Get-ContentUtf8 -Path $contentPath | ConvertFrom-Json

$width = 2250
$height = 6000
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic

$backgroundRect = New-Object System.Drawing.Rectangle 0, 0, $width, $height
$backgroundBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($backgroundRect, (New-Color 245 249 255), (New-Color 231 242 248), 90)
$graphics.FillRectangle($backgroundBrush, $backgroundRect)

$blobBrush1 = New-Object System.Drawing.SolidBrush((New-Color 39 105 171 35))
$blobBrush2 = New-Object System.Drawing.SolidBrush((New-Color 9 179 169 28))
$blobBrush3 = New-Object System.Drawing.SolidBrush((New-Color 250 173 20 24))
$graphics.FillEllipse($blobBrush1, -180, -120, 980, 780)
$graphics.FillEllipse($blobBrush2, 1280, 220, 760, 760)
$graphics.FillEllipse($blobBrush3, 1500, 4700, 620, 620)

$navy = New-Color 18 50 87
$teal = New-Color 10 140 134
$orange = New-Color 242 145 61
$slate = New-Color 78 96 120
$ink = New-Color 20 32 49
$muted = New-Color 96 111 128
$white = [System.Drawing.Color]::White
$cardBorder = New-Color 207 220 231
$softTeal = New-Color 226 245 243
$softBlue = New-Color 233 240 252
$softOrange = New-Color 253 239 222
$softGray = New-Color 244 247 250

$titleFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 70 -Style ([System.Drawing.FontStyle]::Bold)
$subtitleFont = New-FontSafe -Names @('Segoe UI', 'Leelawadee UI') -Size 26 -Style ([System.Drawing.FontStyle]::Bold)
$introFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 28
$sectionFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 34 -Style ([System.Drawing.FontStyle]::Bold)
$bodyFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 26
$smallBodyFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 23
$statValueFont = New-FontSafe -Names @('Segoe UI', 'Leelawadee UI') -Size 44 -Style ([System.Drawing.FontStyle]::Bold)
$statLabelFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 22
$featureTagFont = New-FontSafe -Names @('Segoe UI', 'Leelawadee UI') -Size 18 -Style ([System.Drawing.FontStyle]::Bold)
$featureTitleFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 28 -Style ([System.Drawing.FontStyle]::Bold)
$featureBodyFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 22
$stepNoFont = New-FontSafe -Names @('Segoe UI', 'Leelawadee UI') -Size 20 -Style ([System.Drawing.FontStyle]::Bold)
$stepFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 23 -Style ([System.Drawing.FontStyle]::Bold)
$benefitFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 25
$creditTitleFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 28 -Style ([System.Drawing.FontStyle]::Bold)
$creditFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 23
$logoFont = New-FontSafe -Names @('Segoe UI', 'Leelawadee UI') -Size 34 -Style ([System.Drawing.FontStyle]::Bold)
$footerFont = New-FontSafe -Names @('Leelawadee UI', 'Segoe UI') -Size 22

$navyBrush = New-Object System.Drawing.SolidBrush($navy)
$tealBrush = New-Object System.Drawing.SolidBrush($teal)
$orangeBrush = New-Object System.Drawing.SolidBrush($orange)
$inkBrush = New-Object System.Drawing.SolidBrush($ink)
$mutedBrush = New-Object System.Drawing.SolidBrush($muted)
$whiteBrush = New-Object System.Drawing.SolidBrush($white)
$cardBrush = New-Object System.Drawing.SolidBrush($white)
$softGrayBrush = New-Object System.Drawing.SolidBrush($softGray)
$softBlueBrush = New-Object System.Drawing.SolidBrush($softBlue)
$softTealBrush = New-Object System.Drawing.SolidBrush($softTeal)
$softOrangeBrush = New-Object System.Drawing.SolidBrush($softOrange)
$borderPen = New-Object System.Drawing.Pen($cardBorder, 3)
$accentPen = New-Object System.Drawing.Pen($orange, 8)
$linePen = New-Object System.Drawing.Pen((New-Color 180 197 214), 4)
$logoBorderPen = New-Object System.Drawing.Pen((New-Color 151 170 190), 4)
$logoBorderPen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash

$heroX = 120
$heroY = 110
$heroW = 2010
$heroH = 980

Fill-RoundedRect -Graphics $graphics -Brush $cardBrush -X $heroX -Y $heroY -Width $heroW -Height $heroH -Radius 48
Draw-RoundedRectBorder -Graphics $graphics -Pen $borderPen -X $heroX -Y $heroY -Width $heroW -Height $heroH -Radius 48

$pillBrush = New-Object System.Drawing.SolidBrush((New-Color 18 50 87 235))
Fill-RoundedRect -Graphics $graphics -Brush $pillBrush -X 170 -Y 170 -Width 360 -Height 60 -Radius 28
$graphics.DrawString($data.subtitle, $subtitleFont, $whiteBrush, 205, 182)

$graphics.DrawString($data.title, $titleFont, $navyBrush, 170, 270)
[void](Draw-WrappedText -Graphics $graphics -Text $data.intro -Font $introFont -Brush $mutedBrush -X 175 -Y 405 -Width 910 -LineHeight 42)

$overviewCardX = 165
$overviewCardY = 560
$overviewCardW = 980
$overviewCardH = 420
Fill-RoundedRect -Graphics $graphics -Brush $softGrayBrush -X $overviewCardX -Y $overviewCardY -Width $overviewCardW -Height $overviewCardH -Radius 34
$graphics.DrawString($data.overview_title, $sectionFont, $inkBrush, 210, 605)

for ($i = 0; $i -lt $data.overview_bullets.Count; $i++) {
    $bulletY = 690 + ($i * 72)
    $graphics.FillEllipse($tealBrush, 215, $bulletY + 8, 20, 20)
    [void](Draw-WrappedText -Graphics $graphics -Text $data.overview_bullets[$i] -Font $smallBodyFont -Brush $inkBrush -X 250 -Y $bulletY -Width 830 -LineHeight 34 -MaxLines 2)
}

$illustrationX = 1320
$illustrationY = 260
$illustrationW = 610
$illustrationH = 640
$illustrationBg = New-Object System.Drawing.SolidBrush((New-Color 233 240 252))
Fill-RoundedRect -Graphics $graphics -Brush $illustrationBg -X $illustrationX -Y $illustrationY -Width $illustrationW -Height $illustrationH -Radius 42

$buildingBrush = New-Object System.Drawing.SolidBrush((New-Color 18 50 87))
$windowBrush = New-Object System.Drawing.SolidBrush((New-Color 247 198 90))
$tealLightBrush = New-Object System.Drawing.SolidBrush((New-Color 10 140 134))
$graphics.FillRectangle($buildingBrush, 1495, 385, 240, 350)
$graphics.FillRectangle($tealLightBrush, 1600, 320, 170, 415)
$graphics.FillRectangle($buildingBrush, 1780, 435, 120, 300)
$graphics.FillRectangle($whiteBrush, 1608, 630, 60, 105)
$graphics.FillRectangle($whiteBrush, 1668, 630, 60, 105)

foreach ($x in @(1518, 1568, 1635, 1685, 1798, 1845)) {
    foreach ($y in @(415, 490, 565)) {
        $graphics.FillRectangle($windowBrush, $x, $y, 26, 34)
    }
}

$graphics.FillEllipse($orangeBrush, 1405, 325, 78, 78)
$graphics.FillEllipse($tealBrush, 1848, 348, 52, 52)
$graphics.FillEllipse($softOrangeBrush, 1415, 765, 78, 78)

$statsY = 1160
$statCardW = 595
$gap = 32
for ($i = 0; $i -lt $data.stats.Count; $i++) {
    $x = 120 + ($i * ($statCardW + $gap))
    $bgBrush = @($softBlueBrush, $softTealBrush, $softOrangeBrush)[$i]
    Fill-RoundedRect -Graphics $graphics -Brush $bgBrush -X $x -Y $statsY -Width $statCardW -Height 220 -Radius 34
    $graphics.DrawString($data.stats[$i].value, $statValueFont, $navyBrush, $x + 45, $statsY + 45)
    [void](Draw-WrappedText -Graphics $graphics -Text $data.stats[$i].label -Font $statLabelFont -Brush $inkBrush -X ($x + 45) -Y ($statsY + 120) -Width 360 -LineHeight 32 -MaxLines 2)
}

$featuresTitleY = 1515
Draw-SectionTitle -Graphics $graphics -Text $data.features_title -X 140 -Y $featuresTitleY -Font $sectionFont -Brush $navyBrush -AccentPen $accentPen

$featureCardW = 880
$featureCardH = 255
$featureStartY = 1615
$featureGapX = 50
$featureGapY = 36

for ($i = 0; $i -lt $data.features.Count; $i++) {
    $col = $i % 2
    $row = [math]::Floor($i / 2)
    $x = 140 + ($col * ($featureCardW + $featureGapX))
    $y = $featureStartY + ($row * ($featureCardH + $featureGapY))

    Fill-RoundedRect -Graphics $graphics -Brush $cardBrush -X $x -Y $y -Width $featureCardW -Height $featureCardH -Radius 34
    Draw-RoundedRectBorder -Graphics $graphics -Pen $borderPen -X $x -Y $y -Width $featureCardW -Height $featureCardH -Radius 34

    $iconBrush = @($tealBrush, $orangeBrush, $navyBrush, $tealBrush, $orangeBrush, $navyBrush, $tealBrush, $orangeBrush)[$i]
    $iconBgBrush = @($softTealBrush, $softOrangeBrush, $softBlueBrush, $softTealBrush, $softOrangeBrush, $softBlueBrush, $softTealBrush, $softOrangeBrush)[$i]
    Fill-RoundedRect -Graphics $graphics -Brush $iconBgBrush -X ($x + 30) -Y ($y + 32) -Width 142 -Height 142 -Radius 32
    $graphics.FillEllipse($iconBrush, $x + 55, $y + 57, 92, 92)
    $graphics.DrawString(($data.features[$i].tag.Substring(0, [Math]::Min(4, $data.features[$i].tag.Length))), $featureTagFont, $whiteBrush, $x + 78, $y + 92)

    Fill-RoundedRect -Graphics $graphics -Brush $softGrayBrush -X ($x + 190) -Y ($y + 34) -Width 160 -Height 40 -Radius 18
    $graphics.DrawString($data.features[$i].tag, $featureTagFont, $mutedBrush, $x + 215, $y + 45)
    $graphics.DrawString($data.features[$i].title, $featureTitleFont, $inkBrush, $x + 190, $y + 92)
    [void](Draw-WrappedText -Graphics $graphics -Text $data.features[$i].body -Font $featureBodyFont -Brush $mutedBrush -X ($x + 190) -Y ($y + 136) -Width 635 -LineHeight 30 -MaxLines 3)
}

$workflowTitleY = 2865
Draw-SectionTitle -Graphics $graphics -Text $data.workflow_title -X 140 -Y $workflowTitleY -Font $sectionFont -Brush $navyBrush -AccentPen $accentPen

$timelineX = 230
$timelineTop = 2980
$timelineBottom = 4310
$graphics.DrawLine($linePen, $timelineX, $timelineTop, $timelineX, $timelineBottom)

for ($i = 0; $i -lt $data.workflow_steps.Count; $i++) {
    $stepY = 3005 + ($i * 220)
    $circleBrush = @($navyBrush, $tealBrush, $orangeBrush, $navyBrush, $tealBrush, $orangeBrush)[$i]
    $panelBrush = @($softBlueBrush, $softTealBrush, $softOrangeBrush, $softBlueBrush, $softTealBrush, $softOrangeBrush)[$i]

    $graphics.FillEllipse($circleBrush, 175, $stepY, 110, 110)
    $graphics.DrawString(("0" + ($i + 1)).Substring(("0" + ($i + 1)).Length - 2), $stepNoFont, $whiteBrush, 208, $stepY + 40)

    Fill-RoundedRect -Graphics $graphics -Brush $panelBrush -X 335 -Y ($stepY - 20) -Width 1645 -Height 150 -Radius 30
    $graphics.DrawString($data.workflow_steps[$i], $stepFont, $inkBrush, 390, $stepY + 18)

    [void](Draw-WrappedText -Graphics $graphics -Text $data.workflow_descriptions[$i] -Font $smallBodyFont -Brush $mutedBrush -X 390 -Y ($stepY + 58) -Width 1450 -LineHeight 30 -MaxLines 2)
}

$benefitsTitleY = 4450
Draw-SectionTitle -Graphics $graphics -Text $data.benefits_title -X 140 -Y $benefitsTitleY -Font $sectionFont -Brush $navyBrush -AccentPen $accentPen

$benefitCardY = 4560
$benefitCardH = 180
$benefitCardW = 930
for ($i = 0; $i -lt $data.benefits.Count; $i++) {
    $col = $i % 2
    $row = [math]::Floor($i / 2)
    $x = 140 + ($col * 1040)
    $y = $benefitCardY + ($row * 210)
    $benefitBg = if ($i % 2 -eq 0) { $softBlueBrush } else { $softGrayBrush }
    Fill-RoundedRect -Graphics $graphics -Brush $benefitBg -X $x -Y $y -Width $benefitCardW -Height $benefitCardH -Radius 30
    $graphics.FillEllipse($orangeBrush, $x + 35, $y + 48, 84, 84)
    $graphics.DrawString('+', $statValueFont, $whiteBrush, $x + 54, $y + 49)
    [void](Draw-WrappedText -Graphics $graphics -Text $data.benefits[$i] -Font $benefitFont -Brush $inkBrush -X ($x + 145) -Y ($y + 45) -Width 730 -LineHeight 34 -MaxLines 3)
}

$creditsY = 5070
$creditsH = 270
Fill-RoundedRect -Graphics $graphics -Brush $cardBrush -X 120 -Y $creditsY -Width 2010 -Height $creditsH -Radius 38
Draw-RoundedRectBorder -Graphics $graphics -Pen $borderPen -X 120 -Y $creditsY -Width 2010 -Height $creditsH -Radius 38
$graphics.DrawString($data.credits_title, $creditTitleFont, $navyBrush, 180, ($creditsY + 48))
[void](Draw-WrappedText -Graphics $graphics -Text $data.team_name -Font $creditFont -Brush $inkBrush -X 180 -Y ($creditsY + 108) -Width 1120 -LineHeight 34 -MaxLines 1)
[void](Draw-WrappedText -Graphics $graphics -Text $data.department -Font $creditFont -Brush $mutedBrush -X 180 -Y ($creditsY + 150) -Width 1120 -LineHeight 34 -MaxLines 1)
[void](Draw-WrappedText -Graphics $graphics -Text $data.advisor -Font $creditFont -Brush $mutedBrush -X 180 -Y ($creditsY + 190) -Width 1120 -LineHeight 34 -MaxLines 1)

$logoX = 1560
$logoY = $creditsY + 38
$logoW = 420
$logoH = 190
Fill-RoundedRect -Graphics $graphics -Brush $softGrayBrush -X $logoX -Y $logoY -Width $logoW -Height $logoH -Radius 28
Draw-RoundedRectBorder -Graphics $graphics -Pen $logoBorderPen -X $logoX -Y $logoY -Width $logoW -Height $logoH -Radius 28
$graphics.DrawString($data.logo_placeholder, $logoFont, $mutedBrush, ($logoX + 125), ($logoY + 68))

$footerY = 5450
$footerRectBrush = New-Object System.Drawing.SolidBrush((New-Color 18 50 87))
Fill-RoundedRect -Graphics $graphics -Brush $footerRectBrush -X 120 -Y $footerY -Width 2010 -Height 270 -Radius 42
[void](Draw-WrappedText -Graphics $graphics -Text $data.footer -Font $footerFont -Brush $whiteBrush -X 185 -Y ($footerY + 75) -Width 1760 -LineHeight 36 -MaxLines 2)
$graphics.DrawString('Suitable for presentation, poster board, or project showcase', $statLabelFont, $softTealBrush, 185, $footerY + 155)

$bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)

$backgroundBrush.Dispose()
$blobBrush1.Dispose()
$blobBrush2.Dispose()
$blobBrush3.Dispose()
$navyBrush.Dispose()
$tealBrush.Dispose()
$orangeBrush.Dispose()
$inkBrush.Dispose()
$mutedBrush.Dispose()
$whiteBrush.Dispose()
$cardBrush.Dispose()
$softGrayBrush.Dispose()
$softBlueBrush.Dispose()
$softTealBrush.Dispose()
$softOrangeBrush.Dispose()
$borderPen.Dispose()
$accentPen.Dispose()
$linePen.Dispose()
$logoBorderPen.Dispose()
$pillBrush.Dispose()
$illustrationBg.Dispose()
$buildingBrush.Dispose()
$windowBrush.Dispose()
$tealLightBrush.Dispose()
$footerRectBrush.Dispose()

$titleFont.Dispose()
$subtitleFont.Dispose()
$introFont.Dispose()
$sectionFont.Dispose()
$bodyFont.Dispose()
$smallBodyFont.Dispose()
$statValueFont.Dispose()
$statLabelFont.Dispose()
$featureTagFont.Dispose()
$featureTitleFont.Dispose()
$featureBodyFont.Dispose()
$stepNoFont.Dispose()
$stepFont.Dispose()
$benefitFont.Dispose()
$creditTitleFont.Dispose()
$creditFont.Dispose()
$logoFont.Dispose()
$footerFont.Dispose()

$graphics.Dispose()
$bitmap.Dispose()

Write-Output $outputPath
