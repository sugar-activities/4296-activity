; Copyright (C) 2008, Vincent Povirk for CodeWeavers
;
; This library is free software; you can redistribute it and/or
; modify it under the terms of the GNU Lesser General Public
; License as published by the Free Software Foundation; either
; version 2 of the License, or (at your option) any later version.
;
; This library is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
; Lesser General Public License for more details.
;
; You should have received a copy of the GNU Lesser General Public
; License along with this library; if not, write to the
; Free Software Foundation, Inc., 59 Temple Place - Suite 330,
; Boston, MA 02111-1307, USA.

; Compiled to setup.exe using AutoHotKey's script compiler (www.autohotkey.com)

#NoEnv
#NoTrayIcon

DownloadWithProgressBar(url, desc, size, file)
{
    global DownloadProgress = 0
    
    ProgressWidth := A_ScreenWidth / 3
    
    ;TODO: internationalize this text
    Gui, Add, Text, , Downloading %desc%...
    Gui, Add, Progress, Range-0-%size% VDownloadProgress w%ProgressWidth%
    Gui, Add, Button, Right GQuit, Cancel
    Gui, Show
    
    SetTimer, UpdateDownloadProgress, 500
    
    UrlDownloadToFile, %url%, %file%

    result := ErrorLevel

    SetTimer, UpdateDownloadProgress, Off

    Gui, Hide
    
    return result

UpdateDownloadProgress:
    FileGetSize, BytesDownloaded, %file%
    GuiControl,, DownloadProgress, %BytesDownloaded%
    
    return

Quit:
    ; UrlDownloadToFile can't be interrupted once it started so we have to end
    ; the process.
    ExitApp
}

UpdateFirefoxShortcut()
{
    RegRead, CurrentVersion, HKEY_LOCAL_MACHINE, Software\Mozilla\Mozilla Firefox, CurrentVersion
    IfEqual, ErrorLevel, 1
        FileCreateShortcut, %A_ScriptDir%\setup.exe setup-firefox, %A_ProgramsCommon%\Install Firefox.lnk
    else
        FileDelete, %A_ProgramsCommon%\Install Firefox.lnk
}

; The thing on the left in IfEqual is a variable name. This compares the first
; argument to setup-firefox
IfEqual, 1, setup-firefox
{
    filename = %A_Temp%\install-firefox.exe
    
    ; TODO: check firefox install
    DownloadWithProgressBar("http://download.mozilla.org/?product=firefox-3.5.2&os=win&lang=en-US", "firefox", 8050536, filename)
    
    IfEqual, ErrorLevel, 1
        ExitApp
    
    RunWait, %filename%
    
    UpdateFirefoxShortcut()
}
else
{
    ;normal pre-init setup
    
    RegWrite, REG_SZ, HKEY_CURRENT_USER, Software\Wine\WineBrowser, Browser, sugar-start-uri

    ;don't ever blink cursors
    IniWrite, -1, %A_WinDir%\win.ini, windows, CursorBlinkRate

    ; work around wine bug 16729
    RegWrite, REG_SZ, HKEY_CURRENT_USER, Control Panel\Desktop, FontSmoothing, 2
    RegWrite, REG_DWORD, HKEY_CURRENT_USER, Control Panel\Desktop, FontSmoothingType, 1
    RegWrite, REG_DWORD, HKEY_CURRENT_USER, Control Panel\Desktop, FontSmoothingGamma, 1400

    FileCreateShortcut, %A_ScriptDir%\7zip\7zFM.exe C:, %A_ProgramsCommon%\Accessories\7-Zip File Manager.lnk, %A_ScriptDir%\7zip

    ; 7zip file associations
    archive_types = 7z rar z zip
    Loop, Parse, archive_types, %A_Space%
    {
        RegWrite, REG_SZ, HKEY_CLASSES_ROOT, .%A_LoopField%, , 7-Zip.%A_LoopField%
        RegWrite, REG_SZ, HKEY_CLASSES_ROOT, 7-Zip.%A_LoopField%, , %A_LoopField% Archive
        RegWrite, REG_SZ, HKEY_CLASSES_ROOT, 7-Zip.%A_LoopField%\DefaultIcon, , %A_ScriptDir%\7zip\7z.dll`,0
        RegWrite, REG_SZ, HKEY_CLASSES_ROOT, 7-Zip.%A_LoopField%\shell\open\command, , "%A_ScriptDir%\7zip\7zFM.exe" "`%1"
    }
    
    UpdateFirefoxShortcut()
}

ExitApp

