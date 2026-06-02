cask "tavern" do
  on_macos do
    version "0.1.3"
    sha256 "702834f002fe46b067689bc9f3f1f0abff6d9e30b9cecaa7832fad6c32c93b5d"

    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-macOS.zip"
    app "Tavern.app"

    zap trash: [
      "~/Library/Application Support/Tavern",
      "~/Library/Preferences/dev.hanthor.Tavern.*",
      "~/Library/Caches/dev.hanthor.Tavern",
    ]
  end

  on_linux do
    version "0.1.3"
    sha256 "4712464d96f67bd75f34f022f5f1761bcd3e6cdabd17dc8c870bd41b4ca6f349"

    url "https://github.com/hanthor/Tavern/releases/download/v#{version}/Tavern-Linux.flatpak"
    container type: :naked

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

  name "Tavern"
  desc "Modern Homebrew client for macOS and Linux built with Python and GTK 4"
  homepage "https://github.com/hanthor/Tavern"

  livecheck do
    url "https://github.com/hanthor/Tavern/releases.atom"
    strategy :github_latest
  end
end
