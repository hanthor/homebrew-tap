require_relative "../lib/wallpaper_casks"

cask "bluefin-wallpapers-extra" do
  os macos: "darwin", linux: "linux"

  version "2026-05-09"

  on_macos do
    sha256 "619dc6807432318f0ce5316d77f77bd6cd4549a1c9509bdba10074f71b742ff2"

    url "https://github.com/ublue-os/artwork/releases/download/bluefin-extra-v#{version}/bluefin-wallpapers-extra-macos.tar.zstd"
  end
  on_linux do
    if File.exist?("/usr/bin/plasmashell")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-extra-v#{version}/bluefin-wallpapers-extra-kde.tar.zstd"
      sha256 "0f690073b3d681da24eb9a349ea33669863d4220733c1997577f705aaa43ee70"
    elsif File.exist?("/usr/bin/gnome-shell") || File.exist?("/usr/bin/mutter")
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-extra-v#{version}/bluefin-wallpapers-extra-gnome.tar.zstd"
      sha256 "73a5e034577a665e56be0e8fe0d54f9fdbd7f61096bf4fa638cede41c07aa2e4"
    else
      url "https://github.com/ublue-os/artwork/releases/download/bluefin-extra-v#{version}/bluefin-wallpapers-extra-png.tar.zstd"
      sha256 "dafdb5e47d0a967b7bcfaeabe4afda0d75575fd7ef28b8120c924fc19c53f02c"
    end
  end

  name "bluefin-wallpapers-extra"
  desc "Extra Wallpapers for Bluefin"
  homepage "https://github.com/ublue-os/artwork"

  livecheck do
    url "https://github.com/ublue-os/artwork.git"
    regex(/bluefin-extra-v?(\d{4}-\d{2}-\d{2})/)
    strategy :github_releases
  end

  preflight_steps do
    on_linux { WallpaperCasks.preflight_home_substitution }
  end

  postflight_steps do
    on_macos do
      WallpaperCasks.postflight_macos("bluefin-wallpapers-extra", display_name: "Bluefin-Extra")
    end
    on_linux { WallpaperCasks.postflight_linux("bluefin", nested_images: true) }
  end

  uninstall_postflight_steps do
    on_macos do
      WallpaperCasks.uninstall_macos("bluefin", display_name: "Bluefin-Extra",
                                              target_name: "bluefin-wallpapers-extra")
    end
    on_linux do
      WallpaperCasks.uninstall_linux("bluefin", target_name: "bluefin-wallpapers-extra")
    end
  end

  zap trash: [
    WallpaperCasks.zap_paths_macos("bluefin", display_name: "Bluefin-Extra"),
    WallpaperCasks.zap_paths_linux("bluefin"),
  ].flatten
end
