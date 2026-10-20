# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/wallpaper_casks"

class WallpaperCasksTest < Minitest::Test
  def setup
    @calls = []
    calls = @calls

    %i[symlink run mkdir_p remove].each do |name|
      method_name = name
      WallpaperCasks.define_singleton_method(method_name) do |*args, **kwargs|
        calls << { name: method_name, args: args, kwargs: kwargs }
      end
    end
  end

  def test_preflight_home_substitution_links_home_and_rewrites_xml
    WallpaperCasks.preflight_home_substitution

    assert_equal(
      {
        name: :symlink,
        args: [".", ".user-home"],
        kwargs: { source_base: :home, overwrite: true },
      },
      @calls.fetch(0),
    )

    run = @calls.fetch(1)
    assert_equal(:run, run[:name])
    assert_equal(["/bin/sh"], run[:args])
    assert_equal("{{staged_path}}", run[:kwargs][:chdir])
    assert_equal(["-eu", "-c", run[:kwargs][:args][2]], run[:kwargs][:args])
    assert_includes(run[:kwargs][:args][2], 'WALLPAPER_HOME=$(readlink .user-home)')
    assert_includes(run[:kwargs][:args][2], "find . -type f -name '*.xml'")
    assert_includes(run[:kwargs][:args][2], "-delete")
  end

  def test_postflight_macos_uses_capitalized_artwork_directory_and_home_symlinks
    WallpaperCasks.postflight_macos("bluefin-wallpapers")

    assert_equal(
      {
        name: :mkdir_p,
        args: ["Library/Desktop Pictures/BluefinWallpapers"],
        kwargs: { base: :home },
      },
      @calls.fetch(0),
    )
    assert_equal(
      {
        name: :symlink,
        args: ["*", "Library/Desktop Pictures/BluefinWallpapers"],
        kwargs: { target_base: :home, source_glob: true, overwrite: true },
      },
      @calls.fetch(1),
    )
  end

  def test_postflight_linux_configures_both_desktop_locations_and_environment
    WallpaperCasks.postflight_linux("bazzite")

    assert_equal(
      [
        {
          name: :mkdir_p,
          args: [".local/share/backgrounds/bazzite"],
          kwargs: { base: :home },
        },
        {
          name: :mkdir_p,
          args: [".local/share/wallpapers/bazzite"],
          kwargs: { base: :home },
        },
        {
          name: :mkdir_p,
          args: [".local/share/gnome-background-properties"],
          kwargs: { base: :home },
        },
      ],
      @calls.first(3),
    )

    run = @calls.fetch(3)
    assert_equal(:run, run[:name])
    assert_equal(["/bin/bash"], run[:args])
    assert_equal("{{staged_path}}", run[:kwargs][:chdir])
    assert_equal(
      { "WALLPAPER_HOME" => "{{staged_path}}/.user-home" },
      run[:kwargs][:env],
    )
    assert_equal(
      [
        ".local/share/backgrounds/bazzite",
        ".local/share/wallpapers/bazzite",
        ".local/share/gnome-background-properties",
      ],
      run[:kwargs][:writable_paths],
    )
    assert_equal(:home, run[:kwargs][:writable_base])
    assert_equal(["-eu", "-c", run[:kwargs][:args][2]], run[:kwargs][:args])
    assert_includes(run[:kwargs][:args][2], "plasmashell")
    assert_includes(run[:kwargs][:args][2], "gnome-shell")
    assert_includes(run[:kwargs][:args][2], "mutter")
    assert_includes(run[:kwargs][:args][2], "gnome-background-properties")
  end

  def test_uninstall_macos_removes_only_matching_wallpaper_symlinks
    WallpaperCasks.uninstall_macos("framework")

    assert_equal(
      {
        name: :remove,
        args: ["Library/Desktop Pictures/Framework/*"],
        kwargs: { base: :home, symlink_target_contains: "/framework/" },
      },
      @calls.fetch(0),
    )
  end

  def test_uninstall_linux_removes_all_wallpaper_locations_for_artwork
    WallpaperCasks.uninstall_linux("aurora")

    assert_equal(
      {
        name: :remove,
        args: [
          [
            ".local/share/backgrounds/aurora/**/*",
            ".local/share/wallpapers/aurora/**/*",
            ".local/share/gnome-background-properties/*-aurora*.xml",
          ],
        ],
        kwargs: { base: :home, symlink_target_contains: "/aurora/" },
      },
      @calls.fetch(0),
    )
  end

  def test_zap_paths_follow_platform_cleanup_locations
    assert_equal(
      "#{Dir.home}/Library/Desktop Pictures/BluefinWallpapers",
      WallpaperCasks.zap_paths_macos("bluefin-wallpapers"),
    )
    assert_equal(
      [
        "#{Dir.home}/.local/share/backgrounds/bluefin",
        "#{Dir.home}/.local/share/gnome-background-properties/bluefin-*.xml",
        "#{Dir.home}/.local/share/wallpapers/bluefin",
      ],
      WallpaperCasks.zap_paths_linux("bluefin"),
    )
    assert_empty(@calls)
  end
end
