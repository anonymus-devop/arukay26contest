$ErrorActionPreference = 'Stop'

$agent = 'C:\Program Files\Meta Spatial Editor\v16\Resources\mse-agent.exe'

function Invoke-Mse {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $raw = (& $agent @Arguments | Out-String).Trim()
    $result = $raw | ConvertFrom-Json
    if (-not $result.success) {
        throw "Meta Spatial Editor rechazó '$($Arguments -join ' ')': $raw"
    }
    return $result.data
}

function Find-ObjectId {
    param([Parameter(Mandatory = $true)][string]$Name)
    $listing = Invoke-Mse @('list-objects')
    $match = @($listing.objects | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
    if ($match.Count -gt 0) { return [string]$match[0].id }
    return $null
}

function Add-Primitive {
    param(
        [string]$Type,
        [string]$Name,
        [double]$X,
        [double]$Y,
        [double]$Z,
        [double]$ScaleX,
        [double]$ScaleY,
        [double]$ScaleZ,
        [double]$R,
        [double]$G,
        [double]$B
    )
    $id = Find-ObjectId $Name
    if (-not $id) {
        Invoke-Mse @('add-primitive', '--type', $Type, '--name', $Name, '--x', "$X", '--y', "$Y", '--z', "$Z") | Out-Null
        $id = Find-ObjectId $Name
    }
    if (-not $id) { throw "No se encontró el ID de $Name después de crearlo." }
    Invoke-Mse @('set-scale', '--id', $id, '--x', "$ScaleX", '--y', "$ScaleY", '--z', "$ScaleZ") | Out-Null
    Invoke-Mse @('set-color', '--id', $id, '--r', "$R", '--g', "$G", '--b', "$B", '--a', '1') | Out-Null
    Write-Host "Creado $Name (id=$id)"
    return $id
}

function Add-Panel {
    param([string]$Name, [double]$X, [double]$Y, [double]$Z)
    $id = Find-ObjectId $Name
    if (-not $id) {
        Invoke-Mse @('add-panel', '--name', $Name, '--x', "$X", '--y', "$Y", '--z', "$Z") | Out-Null
        $id = Find-ObjectId $Name
    }
    if (-not $id) { throw "No se encontró el ID del panel $Name después de crearlo." }
    Write-Host "Creado panel $Name (id=$id)"
    return $id
}

Invoke-Mse @('ping') | Out-Null

# Suelo: el cubo base de MSE mide 0.4 m; escala 7.5 crea un área de 3 x 3 m.
Add-Primitive -Type 'cube' -Name 'GAIrden_Suelo' -X 0 -Y -0.2 -Z 0 -ScaleX 7.5 -ScaleY 0.5 -ScaleZ 7.5 -R 0.18 -G 0.10 -B 0.04 | Out-Null

# Tres bancales de cultivo.
Add-Primitive -Type 'cube' -Name 'Bancal_Humedad' -X -1.2 -Y 0.05 -Z 0 -ScaleX 2.2 -ScaleY 0.6 -ScaleZ 2.2 -R 0.30 -G 0.15 -B 0.05 | Out-Null
Add-Primitive -Type 'cube' -Name 'Bancal_Temperatura' -X 0 -Y 0.05 -Z 0 -ScaleX 2.2 -ScaleY 0.6 -ScaleZ 2.2 -R 0.32 -G 0.17 -B 0.06 | Out-Null
Add-Primitive -Type 'cube' -Name 'Bancal_Luz' -X 1.2 -Y 0.05 -Z 0 -ScaleX 2.2 -ScaleY 0.6 -ScaleZ 2.2 -R 0.28 -G 0.13 -B 0.04 | Out-Null


# Paneles informativos flotantes para la futura conexión con Flask/Firebase.
Add-Panel -Name 'Panel_Humedad' -X -2.0 -Y 1.8 -Z -1.8 | Out-Null
Add-Panel -Name 'Panel_Temperatura' -X 0 -Y 1.8 -Z -1.8 | Out-Null
Add-Panel -Name 'Panel_Luz' -X 2.0 -Y 1.8 -Z -1.8 | Out-Null
Add-Panel -Name 'Panel_Consejo_GAIrden' -X 0 -Y 2.7 -Z -1.4 | Out-Null

Invoke-Mse @('save') | Out-Null
Write-Host 'Escena base de GAIrden creada y guardada.' -ForegroundColor Green
