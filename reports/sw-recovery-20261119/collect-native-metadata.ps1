param([Parameter(Mandatory=$true)][string]$Out)
# Metadata/diagnostic whitelist only: no CAD/journal/archive/dump content reaches output.
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Out) { throw 'Refuse to replace evidence' }
$local=$env:LOCALAPPDATA; $roam=$env:APPDATA
$exits=@('20261031050722_34.4.0.0078','20261031050203_34.4.0.0078','20261031045555_34.4.0.0078')
$archives=@('20261031050722','20261031050203','20261031045555','20261031045000','20261030065635','20261030064748','20261030050305','20261030025132','20261030051101','20261028125802','20261028125337','20261028015350','20261028015414','20261028012048')
$paths=@("$roam/SOLIDWORKS/SOLIDWORKS 2026/swxJRNL.swj","$roam/SOLIDWORKS/SOLIDWORKS 2026/swxJRNL.BAK","$local/CrashDumps/ViewServerV6.exe.71496.dmp","$local/CrashDumps/ViewServerV6.exe.54972.dmp","$local/CrashDumps/ViewServerV6.exe.55124.dmp")
$paths+=@($exits | ForEach-Object {"$local/SOLIDWORKS/CXPD/$_/sldexitapp.xml"})
$paths+="$local/SOLIDWORKS/CXRS/RS_20261031050722_34.4.0.0078.xml"
$paths+=@($archives | ForEach-Object {"$local/SOLIDWORKS/CXPA/$_`_34.4.0.0078.zip"})
$files=@(foreach($path in $paths){
    $public=$path.Replace($env:USERPROFILE,'%USERPROFILE%')
    if (-not(Test-Path -LiteralPath $path -PathType Leaf)) { [ordered]@{path=$public;status='absent'}; continue }
    $f=Get-Item -LiteralPath $path
    $row=[ordered]@{path=$public;status='present';bytes=$f.Length;created_utc=$f.CreationTimeUtc.ToString('o');modified_utc=$f.LastWriteTimeUtc.ToString('o');contents_published=$false}
    # Dump/journal memory is not opened, even to hash it. Existing native XML is diagnostic-only.
    if ($f.Extension -eq '.xml') {
        [xml]$x=[IO.File]::ReadAllText($f.FullName)
        $row.safe_fields=@{}
        foreach($name in @('Version','SWServicePack','FileVersion','ProductVersion','AppVersion','SuiteVersion','HOTFIX','CrashFrequency')) {
            $node=$x.SelectSingleNode('//' + $name)
            if($null -ne $node -and $node.InnerText -match '^[0-9A-Za-z ._-]{0,100}$') { $row.safe_fields[$name]=$node.InnerText }
        }
        $row.exception_count=@($x.SelectNodes('//Exception')).Count
        $diag=@($x.SelectNodes('//Exceptions|//CrashDescription') | ForEach-Object {$_.InnerText}) -join "`n"
        $row.diagnostic_markers=@([regex]::Matches($diag,'(?i)\b(?:[A-Za-z0-9_-]+\.dll|sldworks\.exe|ViewServerV6\.exe|0xc0000005|0x800706BA|0x800706BE|AccessViolation|InsertSketch|FeatureExtrusion3)\b') | ForEach-Object {$_.Value} | Select-Object -Unique)
        $row.raw_diagnostic_text_published=$false
    }
    $row
})
$wer=@(foreach($path in @('C:/ProgramData/Microsoft/Windows/WER/ReportArchive/AppCrash_ViewServerV6.exe_4f383ac5c6d1b9ce2a837f10d4e8b79d5bf8c4_844386b3_c6f7ad77-f208-4995-9de4-5252c7e3c557/Report.wer','C:/ProgramData/Microsoft/Windows/WER/ReportArchive/AppCrash_ViewServerV6.exe_4f383ac5c6d1b9ce2a837f10d4e8b79d5bf8c4_844386b3_4a0b9a77-3843-4718-9929-3db21eb661ab/Report.wer')) {
    try { $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);$stream.Dispose();[ordered]@{path=$path;readable=$true;contents_read=$false} }
    catch { [ordered]@{path=$path;readable=$false;error_type=$_.Exception.GetType().FullName;contents_read=$false} }
})
$data=[ordered]@{schema='sw.recovery.native-metadata.v1';observed_at=[DateTime]::UtcNow.ToString('o');files=$files;wer_access=$wer;paid_calls=0;cad_started=$false;settings_changed=$false;limits=@('No archive, dump or journal contents read; those may contain sealed models or personal information.','Native diagnostic markers alone do not identify a crash cause.','ReportArchive access failure is not report absence.','Filename dates are not process-exit timestamps.')}
[IO.File]::WriteAllText($Out,($data|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$data|ConvertTo-Json -Depth 10
