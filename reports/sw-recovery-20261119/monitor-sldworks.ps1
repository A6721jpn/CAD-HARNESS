param(
    [ValidateSet('Inspect','Apply','Restore')][string]$Mode='Inspect',
    [Parameter(Mandatory=$true)][string]$State,
    [Parameter(Mandatory=$true)][string]$Receipt
)
# Only these per-executable settings; no global monitoring, debugger, launch, reboot or process termination.
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Receipt) { throw 'Refuse to replace receipt' }
$dump=Join-Path $env:LOCALAPPDATA 'CADHarnessRecovery/sw-20261119/dumps'
$wer='SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\sldworks.exe'
$ifeo='SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\sldworks.exe'
$spe='SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\sldworks.exe'
$spec=@(
    @{path=$wer;name='DumpFolder';kind='ExpandString';value=$dump},
    @{path=$wer;name='DumpType';kind='DWord';value=1},
    @{path=$wer;name='DumpCount';kind='DWord';value=2},
    @{path=$ifeo;name='GlobalFlag';kind='DWord';value=512},
    @{path=$spe;name='ReportingMode';kind='DWord';value=2},
    @{path=$spe;name='IgnoreSelfExits';kind='DWord';value=0},
    @{path=$spe;name='LocalDumpFolder';kind='String';value=$dump},
    @{path=$spe;name='DumpType';kind='DWord';value=0},
    @{path=$spe;name='MaxNumberOfDumpFiles';kind='DWord';value=2}
)
$base=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryView]::Registry64)
function Save-New([string]$Path,$Value) {
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 12)+"`n");$stream.Write($bytes,0,$bytes.Length)} finally {$stream.Dispose()}
}
function Read-Value($s) {
    $key=$base.OpenSubKey($s.path,$false)
    try {
        $exists=$null -ne $key -and $key.GetValueNames() -contains $s.name
        [ordered]@{path=$s.path;name=$s.name;key_existed=($null -ne $key);exists=$exists;kind=$(if($exists){[string]$key.GetValueKind($s.name)}else{$null});value=$(if($exists){$key.GetValue($s.name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)}else{$null})}
    } finally {if($key){$key.Dispose()}}
}
function Equal-Value($a,$b) {
    ($a.exists -eq $b.exists) -and (-not $a.exists -or ($a.kind -eq $b.kind -and ($a.value|ConvertTo-Json -Compress) -eq ($b.value|ConvertTo-Json -Compress)))
}
function Set-Value($s,$value,[string]$kind) {
    $key=$base.CreateSubKey($s.path)
    try {
        if($kind -eq 'DWord') { $value=[BitConverter]::ToInt32([BitConverter]::GetBytes([uint32]$value),0) }
        $key.SetValue($s.name,$value,[Microsoft.Win32.RegistryValueKind]::$kind)
    } finally {$key.Dispose()}
}
function Restore-Value($s,$old) {
    if($old.exists){Set-Value $s $old.value $old.kind}
    else { $key=$base.OpenSubKey($s.path,$true);if($key){try{$key.DeleteValue($s.name,$false)}finally{$key.Dispose()}} }
}
$report=[ordered]@{observed_at=[DateTime]::UtcNow.ToString('o');mode=$Mode;registry_view='Registry64';status='FAIL';changed_values=0;dump_directory_created=$false;paid_calls=0;cad_started=$false}
$changed=[Collections.Generic.List[int]]::new()
$before=$null
try {
    if($Mode -eq 'Inspect') {
        $before=[ordered]@{schema='sw.recovery.monitoring.before.v1';at=[DateTime]::UtcNow.ToString('o');dump_folder=$dump;values=@($spec|ForEach-Object {Read-Value $_})}
        Save-New $State $before
        $report.status='INSPECTED_no_changes';$report.before=$before
    } else {
        $before=Get-Content -LiteralPath $State -Raw | ConvertFrom-Json
        if($before.schema -ne 'sw.recovery.monitoring.before.v1' -or $before.dump_folder -ne $dump -or $before.values.Count -ne $spec.Count){throw 'Invalid state schema/folder/count'}
        for($i=0;$i -lt $spec.Count;$i++){
            if($before.values[$i].path -ne $spec[$i].path -or $before.values[$i].name -ne $spec[$i].name){throw 'State is outside fixed scope'}
        }
        $old=$before.values[3]
        $flags=if(-not $old.exists){[uint32]0}elseif($old.kind -eq 'String'){
            [Convert]::ToUInt32(([string]$old.value -replace '^0x',''),16)
        }elseif($old.kind -eq 'DWord'){
            [BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$old.value),0)
        }else{throw 'Unsupported existing GlobalFlag kind'}
        # Preserve all existing IFEO flag bits. Its original kind/value is restored exactly.
        $spec[3].value=$flags -bor [uint32]512
        $principal=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
        if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'BLOCK_admin_required_no_changes'}
        if(@(Get-Process -Name sldworks -ErrorAction SilentlyContinue).Count){throw 'BLOCK_running_SW_no_changes'}
        for($i=0;$i -lt $spec.Count;$i++){
            $expected=if($Mode -eq 'Apply'){$before.values[$i]}else{@{exists=$true;kind=$spec[$i].kind;value=$spec[$i].value}}
            if(-not(Equal-Value (Read-Value $spec[$i]) $expected)){throw 'Registry changed since snapshot; refuse overwrite'}
        }
        if($Mode -eq 'Apply') {
            if(-not(Test-Path -LiteralPath $dump)){[IO.Directory]::CreateDirectory($dump)|Out-Null;$report.dump_directory_created=$true}
            for($i=0;$i -lt $spec.Count;$i++){
                $changed.Add($i)
                Set-Value $spec[$i] $spec[$i].value $spec[$i].kind
                if(-not(Equal-Value (Read-Value $spec[$i]) @{exists=$true;kind=$spec[$i].kind;value=$spec[$i].value})){throw 'Registry readback mismatch'}
            }
            $report.changed_values=$changed.Count;$report.status='APPLIED_readback_verified'
        } else {
            for($i=$spec.Count-1;$i -ge 0;$i--){Restore-Value $spec[$i] $before.values[$i]}
            foreach($path in @($wer,$ifeo,$spe)) {
                $wasPresent=@($before.values|Where-Object {$_.path -eq $path -and $_.key_existed}).Count -gt 0
                $key=$base.OpenSubKey($path,$false)
                if($key){$empty=$key.ValueCount -eq 0 -and $key.SubKeyCount -eq 0;$key.Dispose();if(-not $wasPresent -and $empty){$base.DeleteSubKey($path,$false)}}
            }
            for($i=0;$i -lt $spec.Count;$i++){if(-not(Equal-Value (Read-Value $spec[$i]) $before.values[$i])){throw 'Restore readback mismatch'}}
            $report.changed_values=$spec.Count;$report.status='RESTORED_readback_verified'
        }
    }
} catch {
    $report.error=$_.Exception.Message
    if($Mode -eq 'Apply' -and $changed.Count -gt 0){
        $rollback=@()
        for($j=$changed.Count-1;$j -ge 0;$j--){$i=$changed[$j];try{Restore-Value $spec[$i] $before.values[$i]}catch{$rollback+=$spec[$i].path+'::'+$spec[$i].name}}
        $report.rollback_errors=$rollback;$report.changed_values=$changed.Count;$report.status='FAILED_rollback_attempted_inspect_before_retry'
    }elseif($report.error -like 'BLOCK_*'){$report.status=$report.error}
} finally {$report.after=@($spec|ForEach-Object {Read-Value $_});$base.Dispose()}
Save-New $Receipt $report
$report|ConvertTo-Json -Depth 12
if($report.status -in @('INSPECTED_no_changes','APPLIED_readback_verified','RESTORED_readback_verified')){exit 0}else{exit 2}
