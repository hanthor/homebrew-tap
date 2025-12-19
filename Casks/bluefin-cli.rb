cask "bluefin-cli" do
  version "0.0.1"
  sha256 :no_check

  url "https://github.com/hanthor/bluefin-cli/releases/download/v#{version}/bluefin-cli_#{version}_linux_amd64.tar.gz"
  name "Bluefin CLI"
  desc "Bluefin CLI tool"
  homepage "https://github.com/hanthor/bluefin-cli"

  livecheck do
    url :url
    strategy :github_latest
  end

  binary "bluefin-cli"
end
