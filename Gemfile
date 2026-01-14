# Gemfile

source "https://rubygems.org"

# 明确指定 Jekyll 版本。`~> 4.2` 意味着 4.2.x 系列，
# 这会允许 Bundler 使用 4.4.1，同时也兼容未来 4.2.x 的小更新。
gem "jekyll", "~> 4.2"

# 明确指定 Minimal Mistakes 主题 Gem。
# '~> 4.24' 意味着 4.24.x 系列，这会允许 Bundler 使用你目前安装的 4.27.3。
# 如果你希望锁定到更精确的版本，可以直接写 "4.27.3"。
# 使用 '~> 4.24' 通常是更好的做法，因为它允许主题进行小版本更新。
gem "minimal-mistakes-jekyll", "~> 4.24" # 确保版本号是你想要使用的系列

# jekyll-remote-theme 插件用于从 GitHub 仓库加载主题 (如果你只用 `remote_theme` 配置)。
# 如果你已经在 Gemfile 中直接引入 `minimal-mistakes-jekyll`，那么本地构建时 `jekyll-remote-theme` 就不那么必要了。
# 但为了和 GitHub Actions 的远程主题加载保持一致性，保留它也无害。
gem "jekyll-remote-theme"

# 用于处理网络请求的重试机制，是某些 Gems 的依赖
gem "faraday-retry"

# tzinfo-data 用于处理时区信息，主要用于本地开发环境。
gem "tzinfo-data"

# wdm 是 Windows 平台的文件监视器，用于本地开发服务器的热重载。
# 仅在 Windows 系统上安装。
#gem "wdm", "~> 0.1.0" if Gem.win_platform? # 如果你之前因为安装失败移除了，可以考虑加回来，或保持移除。

# Minimal Mistakes 常用且依赖的 Jekyll 插件。
# 明确列出它们可以确保它们在 Gemfile.lock 中被锁定到兼容版本。
group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-paginate"
  gem "jekyll-sitemap"
  gem "jekyll-gist"
  gem "jemoji"
  gem "jekyll-include-cache"
  gem "jekyll-seo-tag"
  gem "jekyll-last-modified-at"
  gem "jekyll-redirect-from" # Minimal Mistakes also often uses this
  gem "jekyll-archives" # 如果你使用归档功能，可以添加
end

# Add fiddle for future Ruby 4.0.0 compatibility and to silence warnings (可选，但推荐)
# gem "fiddle"