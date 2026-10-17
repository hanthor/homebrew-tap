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
  def self.postflight_macos(artwork_name, display_name: nil)
    display_name ||= desktop_picture_name(artwork_name)
    mkdir_p "Library/Desktop Pictures/#{display_name}", base: :home
    symlink "*", "Library/Desktop Pictures/#{display_name}", target_base: :home, source_glob: true, overwrite: true
  end

  # Linux postflight: install to appropriate desktop environment paths
  def self.postflight_linux(artwork_name, nested_images: false)
    mkdir_p ".local/share/backgrounds/#{artwork_name}", base: :home
    mkdir_p ".local/share/wallpapers/#{artwork_name}", base: :home
    mkdir_p ".local/share/gnome-background-properties", base: :home

    gnome_image_install = if nested_images
      <<~SH
        for file in "$PWD"/images/*; do
          filename=$(basename "$file")
          folder=${filename%.*}
          folder=${folder//-night/}
          folder=${folder//-day/}
          mkdir -p "$destination/$folder"
          ln -sfn "$file" "$destination/$folder/$filename"
        done
      SH
    else
      <<~SH
        for file in "$PWD"/images/* "$PWD"/*.{jpg,jpeg,png,xml}; do
          if [ -f "$file" ]; then
            ln -sfn "$file" "$destination/$(basename "$file")"
          fi
        done
      SH
    end

    fallback_install = if nested_images
      <<~SH
        for file in "$PWD"/*; do
          ln -sfn "$file" "$destination/$(basename "$file")"
        done
      SH
    else
      <<~SH
        for file in "$PWD"/*; do
          if [ -f "$file" ]; then
            ln -sfn "$file" "$destination/$(basename "$file")"
          fi
        done
      SH
    end

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
                         #{gnome_image_install}
                         for file in "$PWD"/gnome-background-properties/*; do
                           ln -sfn "$file" "$WALLPAPER_HOME/.local/share/gnome-background-properties/$(basename "$file")"
                         done
                       else
                         #{fallback_install}
                       fi
                     SH
  end

  # Derive Homebrew's Desktop Pictures directory name from a cask's artwork name.
  def self.desktop_picture_name(artwork_name)
    artwork_name.split("-").map(&:capitalize).join
  end
  private_class_method :desktop_picture_name

  # macOS uninstall postflight
  def self.uninstall_macos(artwork_name, display_name: nil, target_name: nil)
    display_name ||= desktop_picture_name(artwork_name)
    target_name ||= artwork_name
    remove "Library/Desktop Pictures/#{display_name}/*", base: :home, symlink_target_contains: "/#{target_name}/"
  end

  # Linux uninstall postflight
  def self.uninstall_linux(artwork_name, target_name: nil)
    target_name ||= artwork_name
    remove [".local/share/backgrounds/#{artwork_name}/**/*",
            ".local/share/wallpapers/#{artwork_name}/**/*",
            ".local/share/gnome-background-properties/*-#{artwork_name}*.xml"],
           base: :home, symlink_target_contains: "/#{target_name}/"
  end

  # macOS zap cleanup paths
  def self.zap_paths_macos(artwork_name, display_name: nil)
    display_name ||= desktop_picture_name(artwork_name)
    "#{Dir.home}/Library/Desktop Pictures/#{display_name}"
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
