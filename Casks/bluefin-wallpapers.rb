require_relative "../lib/wallpaper_casks"

cask "bluefin-wallpapers" do
  os macos: "darwin", linux: "linux"

  version "2026-10-12"

  on_macos do
    sha256 "afafb174f8d16b374ed1bf467b0c688f2e27fd49c44c5e4aba743c36b2b5fa1a"

    url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-kde.tar.zstd"
      sha256 "07fd86ac83115ab413cc7334d31112ce16ab4c3d51e3199c39dac7246012cc47"

    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-gnome.tar.zstd"
      sha256 "c6cd3fb5c6f14472b0ced070d2d9f5ac374197305feb81ab4026cae22d2d1eb5"

    else
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-png.tar.zstd"
      sha256 "28617c0843753c26a98adf08c1b2f9779a7ce397d1d9beee1ed115b82d409cfa"

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
