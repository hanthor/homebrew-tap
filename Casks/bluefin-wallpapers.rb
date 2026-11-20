require_relative "../lib/wallpaper_casks"

cask "bluefin-wallpapers" do
  os macos: "darwin", linux: "linux"

  version "2026-11-19"

  on_macos do
    sha256 "afafb174f8d16b374ed1bf467b0c688f2e27fd49c44c5e4aba743c36b2b5fa1a"

    url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-kde.tar.zstd"
      sha256 "7e6db092c6ad8eff0c79c54e8fb457c956f785f8d0b29f781fc7f21e7abf1040"

    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-gnome.tar.zstd"
      sha256 "8ece06d4191ff33ab8f9dda8461b56cb033e766343ec96de0f98d3fd4dcebd96"

    else
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-png.tar.zstd"
      sha256 "5af11518ebc6c07466dbb7d538d954352c1b7ffe452097d7883a7452312bad7c"

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
