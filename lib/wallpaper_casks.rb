# Shared helpers for wallpaper cask setup and installation

module WallpaperCasks
  # Linux preflight: symlink home and substitute ~ in XML files
  def self.preflight_home_substitution
    symlink ".", ".user-home", source_base: :home, overwrite: true
    run "/bin/sh", args: ["-eu", "-c", <<~'SH'], chdir: "{{staged_path}}"
      WALLPAPER_HOME=$(readlink .user-home)
      replacement=$(printf '%s' "$WALLPAPER_HOME" | sed 's/[\\&|]/\\&/g')
      find . -type f -name '*.xml' -exec sed -i.brew-home-backup "s|~|$replacement|g" {} +
      find . -type f -name '*.xml.brew-home-backup' -delete
    SH
  end

  # macOS postflight: symlink to Desktop Pictures folder
  def self.postflight_macos(artwork_name)
    capitalized = artwork_name.split("-").map(&:capitalize).join
    mkdir_p "Library/Desktop Pictures/#{capitalized}", base: :home
    symlink "*", "Library/Desktop Pictures/#{capitalized}", target_base: :home, source_glob: true, overwrite: true
  end

  # Linux postflight: install to appropriate desktop environment paths
  def self.postflight_linux(artwork_name)
    mkdir_p ".local/share/backgrounds/#{artwork_name}", base: :home
    mkdir_p ".local/share/wallpapers/#{artwork_name}", base: :home
    mkdir_p ".local/share/gnome-background-properties", base: :home
    run "/bin/bash", chdir: "{{staged_path}}",
                     env: { "WALLPAPER_HOME" => "{{staged_path}}/.user-home" },
                     writable_paths: [".local/share/backgrounds/#{artwork_name}",
                                      ".local/share/wallpapers/#{artwork_name}",
                                      ".local/share/gnome-background-properties"],
                     writable_base: :home,
                     args: ["-eu", "-c", <<~SH]
                       shopt -s nullglob
                       destination="$WALLPAPER_HOME/.local/share/backgrounds/#{artwork_name}"
                       if [ -e /usr/bin/plasmashell ]; then
                         destination="$WALLPAPER_HOME/.local/share/wallpapers/#{artwork_name}"
                         for file in "$PWD"/*; do ln -sfn "$file" "$destination/$(basename "$file")"; done
                       elif [ -e /usr/bin/gnome-shell ] || [ -e /usr/bin/mutter ]; then
                         for file in "$PWD"/images/* "$PWD"/*.{jpg,jpeg,png,xml}; do
                           if [ -f "$file" ]; then
                             ln -sfn "$file" "$destination/$(basename "$file")"
                           fi
                         done
                         for file in "$PWD"/gnome-background-properties/*; do
                           ln -sfn "$file" "$WALLPAPER_HOME/.local/share/gnome-background-properties/$(basename "$file")"
                         done
                       else
                         for file in "$PWD"/*; do
                           if [ -f "$file" ]; then
                             ln -sfn "$file" "$destination/$(basename "$file")"
                           fi
                         done
                       fi
                     SH
  end

  # macOS uninstall postflight
  def self.uninstall_macos(artwork_name)
    capitalized = artwork_name.split("-").map(&:capitalize).join
    remove "Library/Desktop Pictures/#{capitalized}/*", base: :home, symlink_target_contains: "/#{artwork_name}/"
  end

  # Linux uninstall postflight
  def self.uninstall_linux(artwork_name)
    remove [".local/share/backgrounds/#{artwork_name}/**/*",
            ".local/share/wallpapers/#{artwork_name}/**/*",
            ".local/share/gnome-background-properties/*-#{artwork_name}*.xml"],
           base: :home, symlink_target_contains: "/#{artwork_name}/"
  end

  # macOS zap cleanup paths
  def self.zap_paths_macos(artwork_name)
    capitalized = artwork_name.split("-").map(&:capitalize).join
    "#{Dir.home}/Library/Desktop Pictures/#{capitalized}"
  end

  # Linux zap cleanup paths
  def self.zap_paths_linux(artwork_name)
    [
      "#{Dir.home}/.local/share/backgrounds/#{artwork_name}",
      "#{Dir.home}/.local/share/gnome-background-properties/#{artwork_name}-*.xml",
      "#{Dir.home}/.local/share/wallpapers/#{artwork_name}",
    ]
  end
end
