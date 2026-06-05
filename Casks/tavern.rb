cask "tavern" do
  version "0.1.3"
  sha256 "702834f002fe46b067689bc9f3f1f0abff6d9e30b9cecaa7832fad6c32c93b5d"

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
