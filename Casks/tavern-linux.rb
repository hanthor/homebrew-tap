cask "tavern-linux" do
  version "0.1.3"
  sha256 "4712464d96f67bd75f34f022f5f1761bcd3e6cdabd17dc8c870bd41b4ca6f349"

  url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.flatpak"
  container type: :naked
  name "Tavern"
  desc "Modern Homebrew client for Linux built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  postflight do
    system_command "flatpak",
      args: ["install", "--user", "--noninteractive", staged_path/"Tavern-Linux.flatpak"],
      sudo: false
  end

  uninstall_postflight do
    system_command "flatpak",
      args: ["remove", "--user", "--noninteractive", "dev.hanthor.Tavern"],
      print_stderr: false,
      sudo: false
  rescue StandardError
    nil
  end

  zap trash: "~/.var/app/dev.hanthor.Tavern"
end
