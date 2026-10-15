require_relative "../lib/wallpaper_casks"

cask "bluefin-wallpapers" do
  os macos: "darwin", linux: "linux"

  version "2026-08-21"

  on_macos do
    sha256 "afafb174f8d16b374ed1bf467b0c688f2e27fd49c44c5e4aba743c36b2b5fa1a"

    url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-kde.tar.zstd"
      sha256 "d1c3b022e5ff0532e2727de76bc9bc8fb2efb74c6201c4d1cda55dbbc3826be9"

    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-gnome.tar.zstd"
      sha256 "b3c5332f28c06265aa39284c0e1fad5ec970860d06737ebae24072a17cb52bf4"

    else
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-png.tar.zstd"
      sha256 "52cce2d24ef1df7978b432c5f248322af27b416efa334e854f57fc9f99decb51"

    end
  end

  name "bluefin-wallpapers"
  desc "Wallpapers for Bluefin"
  homepage "https://github.com/projectbluefin/artwork"

  livecheck do
    url "https://github.com/ublue-os/artwork.git"
    regex(/bluefin-v?(\d{4}-\d{2}-\d{2})/)
    strategy :github_releases
  end

  preflight_steps do
    on_linux { WallpaperCasks.preflight_home_substitution }
  end

  postflight_steps do
    on_macos { WallpaperCasks.postflight_macos("bluefin") }
    on_linux { WallpaperCasks.postflight_linux("bluefin") }
  end

  uninstall_postflight_steps do
    on_macos { WallpaperCasks.uninstall_macos("bluefin") }
    on_linux { WallpaperCasks.uninstall_linux("bluefin") }
  end

  caveats <<~EOS
    On macOS, add ~/Library/Desktop Pictures/Bluefin in System Settings > Wallpaper > Add Folder.
  EOS
end
