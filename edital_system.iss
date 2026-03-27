; edital_system.iss — Script do Inno Setup para criar instalador do EditalSystem
; Instale o Inno Setup em: https://jrsoftware.org/isinfo.php
; Compile com: iscc edital_system.iss

[Setup]
AppName=Edital System
AppVersion=1.0.0
AppPublisher=Felipe — Edital System
AppPublisherURL=https://www.seusite.com.br
AppSupportURL=https://www.seusite.com.br/suporte
AppUpdatesURL=https://www.seusite.com.br/atualizar
DefaultDirName={autopf}\EditalSystem
DefaultGroupName=Edital System
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=dist\installer
OutputBaseFilename=EditalSystem_Setup_v1.0.0
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; CLIENT APP
Source: "dist\client\EditalSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\client\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Edital System"; Filename: "{app}\EditalSystem.exe"
Name: "{group}\{cm:UninstallProgram,Edital System}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Edital System"; Filename: "{app}\EditalSystem.exe"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\EditalSystem.exe"; Description: "{cm:LaunchProgram,Edital System}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
