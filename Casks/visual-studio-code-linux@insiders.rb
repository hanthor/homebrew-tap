require_relative "../lib/visual_studio_code_cask"

cask "visual-studio-code-linux@insiders" do
  arch arm: "arm64", intel: "x64"
  os linux: "linux"

  version "1.140.0-insider,544a8291f5ad8e671a23da7c13001f9f20cbe6a8"
  sha256 arm:          "1283ab68db65cd2e28dd7d7ed563a082ad8e1e22e4e706dbf0fda393ab7024f2",
         intel:        "86a3c38261230d78bf85763d51be5c4c5bdd72c1c63c0c142e9b749dcef603cf",
         arm64_linux:  "1283ab68db65cd2e28dd7d7ed563a082ad8e1e22e4e706dbf0fda393ab7024f2",
         x86_64_linux: "86a3c38261230d78bf85763d51be5c4c5bdd72c1c63c0c142e9b749dcef603cf"

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

  VisualStudioCodeCask.apply(
    self,
    root: "vscode-insiders",
    executable: "code-insiders",
    tunnel_executable: "code-tunnel-insiders",
    desktop_file: "code-insiders.desktop",
    url_handler_file: "code-insiders-url-handler.desktop",
    desktop_name: "Visual Studio Code - Insiders",
    url_handler_name: "Visual Studio Code Insiders - URL Handler",
    startup_wm_class: "Code - Insiders",
    url_scheme: "vscode-insiders",
    keywords: "vscode",
    zap_paths: [
      "~/.config/Code - Insiders",
      "~/.vscode-insiders",
    ],
  )
end
