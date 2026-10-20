# Shared helpers for AppImage extraction

module AppImageCasks
  # Extract an AppImage into squashfs-root and remove the downloaded archive.
  def self.extract(appimage_path)
    set_permissions appimage_path, "+x", recursive: false
    run appimage_path, args: ["--appimage-extract"], base: :staged_path, chdir: "{{staged_path}}"
    remove appimage_path
  end
end
