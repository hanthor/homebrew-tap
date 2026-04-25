class Oramalama < Formula
  desc "Local AI coding assistant powered by RamaLama"
  homepage "https://github.com/hanthor/oramalama"
  license "Apache-2.0"
  version "0.1.0"

  on_macos do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.0/oramalama_0.1.0_darwin_arm64.tar.gz"
      sha256 "135577bee79adf570107f1c83d614cc7325bd60e4b71921835ea7826a97b0b4d"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.0/oramalama_0.1.0_darwin_amd64.tar.gz"
      sha256 "135577bee79adf570107f1c83d614cc7325bd60e4b71921835ea7826a97b0b4d"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.0/oramalama_0.1.0_linux_arm64.tar.gz"
      sha256 "135577bee79adf570107f1c83d614cc7325bd60e4b71921835ea7826a97b0b4d"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.0/oramalama_0.1.0_linux_amd64.tar.gz"
      sha256 "135577bee79adf570107f1c83d614cc7325bd60e4b71921835ea7826a97b0b4d"
    end
  end

  depends_on "ramalama"
  depends_on "gum"
  depends_on "jq"

  def install
    bin.install "oramalama"
  end

  test do
    assert_match /^oramalama version/, shell_output("#{bin}/oramalama -version")
  end
end
