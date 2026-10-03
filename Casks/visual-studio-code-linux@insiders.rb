cask "visual-studio-code-linux@insiders" do
  arch arm: "arm64", intel: "x64"
  os linux: "linux"

  version "1.141.0-insider,e4685335361dd89ac2b84e47ecc64e2842fd52a9"
  sha256 arm:          "45bcf3a285da08c5e65100471f22af23d0d99179016162f2d5bf86c24c4d7324",
         intel:        "181a75be7af02830a69b5e1770ba138bb29e78ce85d6b481e3c00f66560863c8",
         arm64_linux:  "45bcf3a285da08c5e65100471f22af23d0d99179016162f2d5bf86c24c4d7324",
         x86_64_linux: "181a75be7af02830a69b5e1770ba138bb29e78ce85d6b481e3c00f66560863c8"

  url "https://update.code.visualstudio.com/commit:#{version.csv.second}/linux-#{arch}/insider"
  name "Microsoft Visual Studio Code Insiders"
  name "VS Code Insiders"
  desc "Open-source code editor (Insiders build)"
  homepage "https://code.visualstudio.com/insiders/"

  livecheck do
    url "https://update.code.visualstudio.com/api/update/linux-#{arch}/insider/latest"
    strategy :json do |json|
      version = json["productVersion"]
      build = json["version"]
      next if version.blank? || build.blank?

      "#{version},#{build}"
    end
  end

  depends_on formula: "jq"

  binary "vscode-insiders/bin/code-insiders"
  binary "vscode-insiders/bin/code-tunnel-insiders"
  bash_completion "vscode-insiders/resources/completions/bash/code-insiders"
  zsh_completion  "vscode-insiders/resources/completions/zsh/_code-insiders"
  artifact "vscode-insiders/code-insiders.desktop",
           target: "#{Dir.home}/.local/share/applications/code-insiders.desktop"
  artifact "vscode-insiders/code-insiders-url-handler.desktop",
           target: "#{Dir.home}/.local/share/applications/code-insiders-url-handler.desktop"

  preflight_steps do
    move "VSCode-linux-*", "vscode-insiders", source_glob: true
    run "{{HOMEBREW_PREFIX}}/bin/jq",
        args:        ["del(.updateUrl) | .configurationDefaults[\"update.mode\"] = \"none\"",
                      "{{staged_path}}/vscode-insiders/resources/app/product.json"],
        stdout_path: "product.json"
    # Keep sandbox write declarations out of the not-yet-renamed directory.
    run "/bin/mv",
        args: ["{{staged_path}}/product.json", "{{staged_path}}/vscode-insiders/resources/app/product.json"]

    mkdir_p ".local/share/applications", base: :home
    write_file "code-insiders.desktop", <<~EOS
      [Desktop Entry]
      Name=Visual Studio Code - Insiders
      Comment=Code Editing. Redefined.
      GenericName=Text Editor
      Exec={{HOMEBREW_PREFIX}}/bin/code-insiders %F
      Icon={{staged_path}}/vscode-insiders/resources/app/resources/linux/code.png
      Type=Application
      StartupNotify=false
      StartupWMClass=Code - Insiders
      Categories=TextEditor;Development;IDE;
      MimeType=application/x-code-workspace;
      Actions=new-empty-window;
      Keywords=vscode;

      [Desktop Action new-empty-window]
      Name=New Empty Window
      Exec={{HOMEBREW_PREFIX}}/bin/code-insiders --new-window %F
      Icon={{staged_path}}/vscode-insiders/resources/app/resources/linux/code.png
    EOS
    write_file "code-insiders-url-handler.desktop", <<~EOS
      [Desktop Entry]
      Name=Visual Studio Code Insiders - URL Handler
      Comment=Code Editing. Redefined.
      GenericName=Text Editor
      Exec={{HOMEBREW_PREFIX}}/bin/code-insiders --open-url %U
      Icon={{staged_path}}/vscode-insiders/resources/app/resources/linux/code.png
      Type=Application
      NoDisplay=true
      StartupNotify=true
      Categories=Utility;TextEditor;Development;IDE;
      MimeType=x-scheme-handler/vscode-insiders;
      Keywords=vscode;
    EOS
    run "/bin/mv",
        args: ["{{staged_path}}/code-insiders.desktop", "{{staged_path}}/code-insiders-url-handler.desktop",
               "{{staged_path}}/vscode-insiders/"]
  end

  zap trash: [
    "~/.config/Code - Insiders",
    "~/.vscode-insiders",
  ]
end
