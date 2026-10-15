require_relative "../lib/wallpaper_casks"

cask "framework-wallpapers" do
  os macos: "darwin", linux: "linux"

  version "2025-12-14"

  on_macos do
    sha256 "e3afcfdbb919d84e02b0f99c2e450514db347bd4e7dd37e9fa23fdb72d321841"

    url "https://github.com/ublue-os/artwork/releases/download/framework-v#{version}/framework-wallpapers-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/framework-v#{version}/framework-wallpapers-kde.tar.zstd"
      sha256 "2616c84b94bb3e83bf0576bbb260f2a5f98c06674b69e14db335e79d7e3b03a1"
    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/framework-v#{version}/framework-wallpapers-gnome.tar.zstd"
      sha256 "8affb9c512d39fc0c665608939815e1eab7062bf1a01c3deab23de367216efc9"
    else
      url "https://github.com/ublue-os/artwork/releases/download/framework-v#{version}/framework-wallpapers-png.tar.zstd"
      sha256 "2da39f34cb2131861da2adca1d03a6b25b0714b2e7d2686b4d14f7ed8c60e8eb"
    end
  end

  name "framework-wallpapers"
  desc "Wallpapers for Framework laptops"
  homepage "https://github.com/projectbluefin/artwork"

  livecheck do
    url "https://github.com/ublue-os/artwork.git"
    regex(/framework-v?(\d{4}-\d{2}-\d{2})/)
    strategy :github_releases
  end

  preflight_steps do
    on_linux { WallpaperCasks.preflight_home_substitution }
  end

  postflight_steps do
    on_macos { WallpaperCasks.postflight_macos("framework") }
    on_linux { WallpaperCasks.postflight_linux("framework") }
  end

  uninstall_postflight_steps do
    on_macos { WallpaperCasks.uninstall_macos("framework") }
    on_linux { WallpaperCasks.uninstall_linux("framework") }
  end

  zap trash: [
    WallpaperCasks.zap_paths_macos("framework"),
    WallpaperCasks.zap_paths_linux("framework"),
  ].flatten
end
