cask "tavern" do
  version "0.1.6"

  name "Tavern"
  desc "Modern Homebrew client built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  on_macos do
    sha256 "52e377ec0e822badeecd65b4a9f9b17f62caa5e820aac1d4860b2ff865c071dc"
    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-macOS.zip"

    app "Tavern.app"

    zap trash: [
      "~/Library/Application Support/Tavern",
      "~/Library/Preferences/dev.hanthor.Tavern.*",
      "~/Library/Caches/dev.hanthor.Tavern",
    ]
  end

  on_linux do
    sha256 "514d4ffe2a2f757369b41863a4f63fbbb222c429652803ebc081cb16ba21ac25"
    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.AppImage"

    binary "squashfs-root/AppRun", target: "tavern"

    artifact "squashfs-root/usr/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
             target: "#{Dir.home}/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg"

    artifact "squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop",
             target: "#{Dir.home}/.local/share/applications/dev.hanthor.Tavern.desktop"

    preflight do
      appimage_path = "#{staged_path}/Tavern-Linux.AppImage"
      FileUtils.chmod 0o755, appimage_path
      system_command appimage_path, args: ["--appimage-extract"], chdir: staged_path
      FileUtils.rm appimage_path

      FileUtils.mkdir_p "#{Dir.home}/.local/share/applications"
      FileUtils.mkdir_p "#{Dir.home}/.local/share/icons/hicolor/scalable/apps"

      desktop = File.read("#{staged_path}/squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop")
      desktop.gsub!(%r{^Exec=.*}, "Exec=#{HOMEBREW_PREFIX}/bin/tavern")
      desktop.gsub!(%r{^Icon=.*}, "Icon=dev.hanthor.Tavern")
      File.write("#{staged_path}/squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop", desktop)
    end

    postflight do
      system_command "gtk-update-icon-cache",
        args: ["-qtf", "#{Dir.home}/.local/share/icons/hicolor"],
        sudo: false
    rescue StandardError
      nil
    end

    zap trash: [
      "~/.local/share/applications/dev.hanthor.Tavern.desktop",
      "~/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
      "~/.local/share/dev.hanthor.Tavern",
      "~/.config/dev.hanthor.Tavern",
      "~/.cache/tavern",
    ]
  end
end
