class Oramalama < Formula
  desc "Local AI coding assistant powered by RamaLama"
  homepage "https://github.com/hanthor/oramalama"
  license "Apache-2.0"
  version "0.1.1"

  on_macos do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.1/oramalama_0.1.1_darwin_arm64.tar.gz"
      sha256 "378a2c44f8953e0ed636500a94702d007a1455dc6e0902d1aeb1fe7228b00899"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.1/oramalama_0.1.1_darwin_amd64.tar.gz"
      sha256 "378a2c44f8953e0ed636500a94702d007a1455dc6e0902d1aeb1fe7228b00899"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.1/oramalama_0.1.1_linux_arm64.tar.gz"
      sha256 "378a2c44f8953e0ed636500a94702d007a1455dc6e0902d1aeb1fe7228b00899"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.1/oramalama_0.1.1_linux_amd64.tar.gz"
      sha256 "378a2c44f8953e0ed636500a94702d007a1455dc6e0902d1aeb1fe7228b00899"
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
