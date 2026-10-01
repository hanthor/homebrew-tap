cask "tavern" do
  version "0.1.8"

  on_macos do
    sha256 "3e72e136b55696e1a3d1b6c08e5818d13aa0aaa1e75f1ccd425e36894d1780d0"

    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-macOS.zip"
  end
  on_macos do
    app "Tavern.app"
  end
  on_linux do
    sha256 "0c34891fd9881bf9fe1238d6c4886fc9096f97782f293a4cb10631ee5828881b"

    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.AppImage"
  end
  on_linux do
    depends_on formula: "pygobject3"

    binary "squashfs-root/AppRun", target: "tavern"
    artifact "squashfs-root/usr/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
             target: "#{Dir.home}/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg"
    artifact "squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop",
             target: "#{Dir.home}/.local/share/applications/dev.hanthor.Tavern.desktop"

    preflight_steps do
      set_permissions "Tavern-Linux.AppImage", "+x", recursive: false
      run "Tavern-Linux.AppImage", args: ["--appimage-extract"], base: :staged_path, chdir: "{{staged_path}}"
      remove "Tavern-Linux.AppImage"
      symlink ".", ".user-home", source_base: :home, overwrite: true
      mkdir_p ".local/share/applications", base: :home
      mkdir_p ".local/share/icons/hicolor/scalable/apps", base: :home
      # The extracted files do not exist until the AppImage has been extracted.
      # AppRun resolves its own directory from $0, which is the Homebrew bin
      # symlink; resolve the symlink first, and point Tavern at the bundled
      # data and locale directories instead of the meson prefix.
      run "/bin/sed", args: [
        "-i",
        "-e", 's|this_dir="$(readlink -f "$(dirname "$0")")"|this_dir="$(dirname "$(readlink -f "$0")")"|',
        "-e", 's|^exec "$this_dir"/AppRun.wrapped "$@"|' \
              'export TAVERN_DATADIR="$this_dir/usr/share/tavern"\n' \
              'export TAVERN_LOCALEDIR="$this_dir/usr/share/locale"\n' \
              'exec "$this_dir"/AppRun.wrapped "$@"|',
        "{{staged_path}}/squashfs-root/AppRun"
      ]
      run "/bin/sed", args: [
        "-i",
        "-e", "s|^Exec=.*|Exec={{HOMEBREW_PREFIX}}/bin/tavern|",
        "-e", "s|^Icon=.*|Icon=dev.hanthor.Tavern|",
        "{{staged_path}}/squashfs-root/usr/share/applications/dev.hanthor.Tavern.desktop"
      ]
    end

    postflight_steps do
      # Refresh the per-user icon cache if one exists; failure here is harmless.
      run "/bin/sh", chdir:          "{{staged_path}}",
                     must_succeed:   false,
                     writable_paths: [".local/share/icons/hicolor"],
                     writable_base:  :home,
                     args:           ["-c", <<~SH]
                       icons="$(readlink .user-home)/.local/share/icons/hicolor"
                       if command -v gtk-update-icon-cache >/dev/null 2>&1; then
                         gtk-update-icon-cache -qtf "$icons" || true
                       fi
                     SH
    end
  end

  name "Tavern"
  desc "Modern Homebrew client built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  zap trash: [
    "~/.cache/tavern",
    "~/.config/dev.hanthor.Tavern",
    "~/.local/share/applications/dev.hanthor.Tavern.desktop",
    "~/.local/share/dev.hanthor.Tavern",
    "~/.local/share/icons/hicolor/scalable/apps/dev.hanthor.Tavern.svg",
    "~/Library/Application Support/Tavern",
    "~/Library/Caches/dev.hanthor.Tavern",
    "~/Library/Preferences/dev.hanthor.Tavern.*",
  ]
end
