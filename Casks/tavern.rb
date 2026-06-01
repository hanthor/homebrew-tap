cask "tavern" do
  version "0.1.1"
  sha256 "55bedc8d075e85b3ac60d8a229495d71e74c34b77c39ebef4580ef98667ce6d7"

  url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-macOS.zip"
  name "Tavern"
  desc "Modern Homebrew client for macOS built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end

  app "Tavern.app"

  zap trash: [
    "~/Library/Application Support/Tavern",
    "~/Library/Preferences/dev.hanthor.Tavern.*",
    "~/Library/Caches/dev.hanthor.Tavern",
  ]
end
