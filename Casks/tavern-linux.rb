cask "tavern-linux" do
  version "0.1.3"

  url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.flatpak"
  name "Tavern"
  desc "Modern Homebrew client built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  deprecate! date: "2026-06-14", because: "merged into the `tavern` cask; use `brew install --cask tavern` instead"
end
