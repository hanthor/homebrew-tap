require_relative "../lib/visual_studio_code_cask"

cask "visual-studio-code-linux" do
  arch arm: "arm64", intel: "x64"
  os linux: "linux"

  version "1.140.0,07f806f999227108933c2e30515b26eecc1fda74"
  sha256 arm:          "9609a7655c4bc2a101b343ff22aa91f6678b46d9565b914c0608bd7f2e577fa6",
         intel:        "d32031e9e213d59532af3cf32fcb8b357a1cdd10417967b4f5b5ba30436dc0dc",
         arm64_linux:  "9609a7655c4bc2a101b343ff22aa91f6678b46d9565b914c0608bd7f2e577fa6",
         x86_64_linux: "d32031e9e213d59532af3cf32fcb8b357a1cdd10417967b4f5b5ba30436dc0dc"

  url "https://update.code.visualstudio.com/commit:#{version.csv.second}/linux-#{arch}/stable"
  name "Microsoft Visual Studio Code"
  name "VS Code"
  desc "Open-source code editor"
  homepage "https://code.visualstudio.com/"

  livecheck do
    url "https://update.code.visualstudio.com/api/update/linux-#{arch}/stable/latest"
    strategy :json do |json|
      version = json["productVersion"]
      build = json["version"]
      next if version.blank? || build.blank?

      "#{version},#{build}"
    end
  end

  VisualStudioCodeCask.apply(
    self,
    root: "vscode",
    executable: "code",
    tunnel_executable: "code-tunnel",
    desktop_file: "code.desktop",
    url_handler_file: "code-url-handler.desktop",
    desktop_name: "Visual Studio Code",
    url_handler_name: "Visual Studio Code - URL Handler",
    startup_wm_class: "Code",
    url_scheme: "vscode",
    keywords: "vscode",
    localized_names: [
      ["cs", "Nové prázdné okno"],
      ["de", "Neues leeres Fenster"],
      ["es", "Nueva ventana vacía"],
      ["fr", "Nouvelle fenêtre vide"],
      ["it", "Nuova finestra vuota"],
      ["ja", "新しい空のウィンドウ"],
      ["ko", "새 빈 창"],
      ["ru", "Новое пустое окно"],
      ["zh_CN", "新建空窗口"],
      ["zh_TW", "開新空視窗"],
    ],
    zap_paths: [
      "~/.config/Code",
      "~/.vscode",
    ],
  )
end
