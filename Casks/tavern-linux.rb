cask "tavern-linux" do
  version "0.1.1"
  sha256 "0b2e6f3d1d409ea66742293c0708d7bcdaa99543b674be8544e4a821af2d4f0c"

  url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.flatpak"
  name "Tavern"
  desc "Modern Homebrew client for Linux built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  depends_on formula: "flatpak"

  postflight do
    system "flatpak", "install", "--user", "--noninteractive", staged_path/"Tavern-Linux.flatpak"
  end

  uninstall_postflight do
    system "flatpak", "remove", "--user", "--noninteractive", "dev.hanthor.Tavern", err: :ignore
  end

  zap trash: "~/.var/app/dev.hanthor.Tavern"
end
