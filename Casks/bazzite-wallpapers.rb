require_relative "../lib/wallpaper_casks"

cask "bazzite-wallpapers" do
  os macos: "darwin", linux: "linux"

  version "2026-06-07"

  on_macos do
    sha256 "eddccab5e33be32a3e159f4a5cc54e4f1b2a3f2e1ba433dc3919b98f066e7012"

    url "https://github.com/ublue-os/artwork/releases/download/bazzite-v#{version}/bazzite-wallpapers-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/bazzite-v#{version}/bazzite-wallpapers-kde.tar.zstd"
      sha256 "8e63d4567b54a8c8f7c5b4e5b5c5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"

    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/bazzite-v#{version}/bazzite-wallpapers-gnome.tar.zstd"
      sha256 "d2b4a5c5e7f5b5c5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"

    else
      url "https://github.com/ublue-os/artwork/releases/download/bazzite-v#{version}/bazzite-wallpapers-png.tar.zstd"
      sha256 "a5c5e7f5b5c5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f"

    end
  end

  name "bazzite-wallpapers"
  desc "Wallpapers for Bazzite"
  homepage "https://github.com/projectbluefin/artwork"

  livecheck do
    url "https://github.com/ublue-os/artwork.git"
    regex(/bazzite-v?(\d{4}-\d{2}-\d{2})/)
    strategy :github_releases
  end

  preflight_steps do
    on_linux { WallpaperCasks.preflight_home_substitution }
  end

  postflight_steps do
    on_macos { WallpaperCasks.postflight_macos("bazzite") }
    on_linux { WallpaperCasks.postflight_linux("bazzite") }
  end

  uninstall_postflight_steps do
    on_macos { WallpaperCasks.uninstall_macos("bazzite") }
    on_linux { WallpaperCasks.uninstall_linux("bazzite") }
  end

  caveats <<~EOS
    On macOS, add ~/Library/Desktop Pictures/Bazzite in System Settings > Wallpaper > Add Folder.
  EOS
end
