cask "tavern" do
  version "0.1.9"

  name "Tavern"
  desc "Modern Homebrew client built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  on_macos do
    sha256 "ae32e225e823d1654c2e83f98b93f87a9e153d71af5b5f7526ad391d910b1010"
    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-macOS.zip"

    app "Tavern.app"

    zap trash: [
      "~/Library/Application Support/Tavern",
      "~/Library/Caches/dev.hanthor.Tavern",
      "~/Library/Preferences/dev.hanthor.Tavern.*",
    ]
  end

  on_linux do
    sha256 "0176f7a3c7372b04dfeda34405068edab8349bc017b48c016b0ea6d40e1e70b3"
    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.AppImage"

    depends_on formula: "pygobject3"

    binary "squashfs-root/AppRun", target: "tavern"

    artifact "squashfs-root/usr/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
             target: "#{Dir.home}/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg"

    artifact "squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop",
             target: "#{Dir.home}/.local/share/applications/dev.hanthor.Tavern.desktop"

    preflight do
      appimage_path = "#{staged_path}/Tavern-Linux.AppImage"
      FileUtils.chmod 0755, appimage_path
      system_command appimage_path, args: ["--appimage-extract"], chdir: staged_path
      FileUtils.rm appimage_path

      # PATCH: fix AppRun's $0-based path resolution.
      # When symlinked from HOMEBREW_PREFIX/bin, $0 is the symlink's dir,
      # not the squashfs-root where the script actually lives.
      # Replace:  this_dir="$(readlink -f "$(dirname "$0")")"
      # With:     this_dir="$(dirname "$(readlink -f "$0")")"
      apprun_path = "#{staged_path}/squashfs-root/AppRun"
      apprun = File.read(apprun_path)
      apprun.gsub!('this_dir="$(readlink -f "$(dirname "$0")")"',
                   'this_dir="$(dirname "$(readlink -f "$0")")"')
      # PATCH: set TAVERN_DATADIR so the Python script finds gresource/icons
      # relative to the AppDir, not the hardcoded meson prefix (/usr/share/tavern)
      apprun.sub!('exec "$this_dir"/AppRun.wrapped "$@"',
                  "export TAVERN_DATADIR=\"$this_dir/usr/share/tavern\"\n" \
                  "export TAVERN_LOCALEDIR=\"$this_dir/usr/share/locale\"\n" \
                  'exec "$this_dir"/AppRun.wrapped "$@"')
      File.write(apprun_path, apprun)

      FileUtils.mkdir_p "#{Dir.home}/.local/share/applications"
      FileUtils.mkdir_p "#{Dir.home}/.local/share/icons/hicolor/scalable/apps"

      desktop = File.read("#{staged_path}/squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop")
      desktop.gsub!(/^Exec=.*/, "Exec=#{HOMEBREW_PREFIX}/bin/tavern")
      desktop.gsub!(/^Icon=.*/, "Icon=dev.hanthor.Tavern")
      File.write("#{staged_path}/squashfs-root/dev.hanthor.Tavern.desktop", desktop)
    end

    postflight do
      system_command "gtk-update-icon-cache",
                     args: ["-qtf", "#{Dir.home}/.local/share/icons/hicolor"],
                     sudo: false
    rescue
      nil
    end

    zap trash: [
      "~/.cache/tavern",
      "~/.config/dev.hanthor.Tavern",
      "~/.local/share/applications/dev.hanthor.Tavern.desktop",
      "~/.local/share/dev.hanthor.Tavern",
      "~/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
    ]
  end
end
