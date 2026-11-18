param([Parameter(Mandatory=$true)][string]$Out)
# Read-only OS queries. Never starts/binds CAD, changes settings, or reads CAD/gold files.
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Out) { throw 'Refuse to replace an evidence file' }
$start = [DateTimeOffset]::Parse('2026-10-26T00:00:00Z').UtcDateTime
$end = [DateTimeOffset]::Parse('2026-11-05T00:00:00Z').UtcDateTime
$nearStart = [DateTimeOffset]::Parse('2026-10-28T23:00:00Z').UtcDateTime
$nearEnd = [DateTimeOffset]::Parse('2026-10-29T02:00:00Z').UtcDateTime
function Public-Text([string]$Text) {
    if ($null -eq $Text) { return $null }
    $s = $Text.Replace($env:USERPROFILE, '%USERPROFILE%').Replace($env:COMPUTERNAME, '%HOST%')
    if ($env:USERNAME) { $s = [regex]::Replace($s, [regex]::Escape($env:USERNAME), '%USER%', 'IgnoreCase') }
    $s = [regex]::Replace($s, 'C:\\Users\\[^\\\s]+', '%USERPROFILE%', 'IgnoreCase')
    # Do not publish arbitrary filenames/commands from event payloads.
    return $s
}
function Event-Metadata($Event) {
    [ordered]@{ utc=$Event.TimeCreated.ToUniversalTime().ToString('o'); id=$Event.Id; provider=$Event.ProviderName; record_id=$Event.RecordId; level=$Event.LevelDisplayName }
}
function Event-Query([string]$Log, [hashtable]$Filter, [string]$Match='') {
    $filterTable = @{LogName=$Log;StartTime=$start;EndTime=$end}
    foreach ($key in $Filter.Keys) { $filterTable[$key] = $Filter[$key] }
    try {
        $rows = @(Get-WinEvent -FilterHashtable $filterTable -ErrorAction Stop)
        if ($Match) { $rows = @($rows | Where-Object { $_.Message -match $Match }) }
        $published = @($rows | ForEach-Object {
            $e = Event-Metadata $_
            # Only public OS lifecycle/display messages; app events use whitelisted XML values below.
            if ($Log -eq 'System') { $e.message = Public-Text $_.Message }
            if ($Log -eq 'Application') {
                [xml]$xml = $_.ToXml()
                $values = @{}
                foreach ($data in $xml.Event.EventData.Data) {
                    if ($data.Name -in @('AppName','AppVersion','ModuleName','ModuleVersion','ExceptionCode','FaultingOffset','ProcessId','AppStartTime')) {
                        $values[$data.Name] = Public-Text $data.'#text'
                    }
                }
                $e.crash_fields = $values
                $e.subject = if ($_.Message -match '(?i)sldworks') {'sldworks'} elseif ($_.Message -match '(?i)ViewServer') {'ViewServerV6'} else {'graphics_or_sw_helper'}
            }
            $e
        })
        [ordered]@{status='ok';count=$published.Count;events=$published}
    } catch {
        [ordered]@{status=if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') {'no_matching_events'} else {'query_error'};error_id=$_.FullyQualifiedErrorId;message=Public-Text $_.Exception.Message;count=0;events=@()}
    }
}
$retention = @()
foreach ($name in @('System','Application','Microsoft-Windows-TerminalServices-LocalSessionManager/Operational','Security')) {
    try {
        $info = Get-WinEvent -ListLog $name
        $oldest = Get-WinEvent -LogName $name -Oldest -MaxEvents 1
        $retention += [ordered]@{log=$name;enabled=$info.IsEnabled;records=$info.RecordCount;mode=[string]$info.LogMode;max_bytes=$info.MaximumSizeInBytes;oldest_utc=$oldest.TimeCreated.ToUniversalTime().ToString('o');october_window_retained=($oldest.TimeCreated.ToUniversalTime() -le $nearStart)}
    } catch { $retention += [ordered]@{log=$name;status='query_error';error_id=$_.FullyQualifiedErrorId;message=Public-Text $_.Exception.Message} }
}
$os = Get-CimInstance Win32_OperatingSystem
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
$processes = @(Get-Process -Name sldworks,ViewServerV6 -ErrorAction SilentlyContinue | ForEach-Object {
    [ordered]@{name=$_.ProcessName;pid=$_.Id;responding=$_.Responding;session_id=$_.SessionId;started_utc=$_.StartTime.ToUniversalTime().ToString('o')}
})
$sessionQuery = [ordered]@{session_name=$env:SESSIONNAME;method='WTSQuerySessionInformationW';status='unknown'}
try {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RecoveryWts {
  [DllImport("wtsapi32.dll", SetLastError=true)]
  public static extern bool WTSQuerySessionInformationW(IntPtr server, int session, int field, out IntPtr data, out int bytes);
  [DllImport("wtsapi32.dll")]
  public static extern void WTSFreeMemory(IntPtr data);
}
'@
    $buffer=[IntPtr]::Zero; $bytes=0
    if (-not [RecoveryWts]::WTSQuerySessionInformationW([IntPtr]::Zero,(Get-Process -Id $PID).SessionId,16,[ref]$buffer,[ref]$bytes)) {
        throw "WTS query failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    try {
        $protocol=[Runtime.InteropServices.Marshal]::ReadInt16($buffer)
        $sessionQuery.protocol=$protocol
        $sessionQuery.transport=if($protocol -eq 0){'console'}elseif($protocol -eq 2){'RDP'}else{'other'}
        $sessionQuery.status='ok'
    } finally { if ($buffer -ne [IntPtr]::Zero) { [RecoveryWts]::WTSFreeMemory($buffer) } }
} catch { $sessionQuery.status='query_error'; $sessionQuery.error=Public-Text $_.Exception.Message }
$video = @(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,DriverDate,Status,CurrentHorizontalResolution,CurrentVerticalResolution,VideoModeDescription,PNPDeviceID)
$monitors = @(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorConnectionParams -ErrorAction SilentlyContinue | Select-Object Active,VideoOutputTechnology)
$drivers = @(Get-CimInstance Win32_PnPSignedDriver | Where-Object {$_.DeviceClass -eq 'DISPLAY'} | Select-Object DeviceName,DriverVersion,DriverDate,DriverProviderName,InfName,IsSigned)
$data = [ordered]@{
    schema='sw.recovery.host-evidence.v1';observed_at=[DateTime]::UtcNow.ToString('o');paid_calls=0;cad_started=$false;com_bound=$false;settings_changed=$false
    window_utc=@($start.ToString('o'),$end.ToString('o'));interruption_window_utc=@($nearStart.ToString('o'),$nearEnd.ToString('o'))
    last_boot_utc=$os.LastBootUpTime.ToUniversalTime().ToString('o');os_version=$os.Version;os_build=$os.BuildNumber;timezone=(Get-TimeZone).Id
    administrator=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);collector_session_id=(Get-Process -Id $PID).SessionId
    session_query=$sessionQuery;processes=$processes;video=$video;monitor_connections=$monitors;display_drivers=$drivers;event_retention=$retention
    lifecycle=(Event-Query 'System' @{Id=@(1,12,13,41,1074,6005,6006,6008)})
    display=(Event-Query 'System' @{Id=@(4101)})
    gpu_provider=(Event-Query 'System' @{ProviderName=@('nvlddmkm','Microsoft-Windows-DxgKrnl','Microsoft-Windows-WHEA-Logger')})
    updates=(Event-Query 'System' @{ProviderName='Microsoft-Windows-WindowsUpdateClient'})
    application_crashes=(Event-Query 'Application' @{Id=@(1000,1001,1002)} '(?i)sldworks|ViewServer|nvoglv|opengl|swShell')
    sessions=(Event-Query 'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational' @{Id=@(21,22,23,24,25,39,40,41)})
    audit_sessions=$(if (@($retention | Where-Object {$_.log -eq 'Security' -and $_.status -eq 'query_error'}).Count) {
        [ordered]@{status='access_unverified_do_not_infer_absence';count=0;events=@()}
    } else { Event-Query 'Security' @{Id=@(4634,4647,4778,4779)} })
    limits=@('Event absence is not proof when retention/access is incomplete.','No journal, dump memory, CAD, private gold or sealed seed contents were read.','Only app crash metadata is public; arbitrary app messages/commands/document names are omitted.')
}
$json = $data | ConvertTo-Json -Depth 15
[IO.File]::WriteAllText($Out, $json + "`n", [Text.UTF8Encoding]::new($false))
[ordered]@{out=$Out;observed_at=$data.observed_at;last_boot_utc=$data.last_boot_utc;administrator=$data.administrator;processes=$data.processes;retention=$retention;counts=[ordered]@{lifecycle=$data.lifecycle.count;display=$data.display.count;gpu=$data.gpu_provider.count;updates=$data.updates.count;crashes=$data.application_crashes.count;sessions=$data.sessions.count;audit=$data.audit_sessions.count}} | ConvertTo-Json -Depth 8
