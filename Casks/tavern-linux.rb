cask "tavern-linux" do
  version "0.1.5"
  sha256 "b0c4b626fa9d75a249843b194d1d6129ad3b0bc11e3f2f4e947b6d705ba8e37c"

  url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.flatpak"
  name "Tavern"
  desc "Modern Homebrew client for Linux built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  container type: :naked

  postflight do
    system_command "flatpak",
                   args: ["install", "--user", "--noninteractive", staged_path/"Tavern-Linux.flatpak"],
                   sudo: false
  end

  uninstall_postflight do
    system_command "flatpak",
                   args:         ["remove", "--user", "--noninteractive", "dev.hanthor.Tavern"],
                   print_stderr: false,
                   sudo:         false
  rescue
    nil
  end

  zap trash: "~/.var/app/dev.hanthor.Tavern"
end
