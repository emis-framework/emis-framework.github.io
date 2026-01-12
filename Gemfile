# Gemfile

source "https://rubygems.org"

# github-pages gem 包含了 Jekyll 及其在 GitHub Pages 上支持的所有插件。
# 它还会安装兼容的 Jekyll 版本。强烈推荐使用它来确保本地环境与 GitHub Pages 一致。
gem "github-pages"

# jekyll-remote-theme 插件用于从 GitHub 仓库加载主题 (如 Minimal Mistakes)。
# 虽然 github-pages gem 可能已经包含它，但为了清晰和兼容性，最好显式声明。
gem "jekyll-remote-theme"

# tzinfo-data 用于处理时区信息，主要用于本地开发环境。
# GitHub Pages 构建环境不一定需要，但保留无害。
gem "tzinfo-data"

# wdm 是 Windows 平台的文件监视器，用于本地开发服务器的热重载。
# 仅在 Windows 系统上安装。
gem "wdm", "~> 0.1.0" if Gem.win_platform?

# 如果你需要使用 GitHub Pages 不支持的自定义插件 (例如 jekyll-algolia)，
# 你将不能依赖 GitHub Pages 的默认构建。
# 这种情况下，你需要配置 GitHub Actions 来手动构建你的站点。
# 如果你已经配置了 GitHub Actions，并且需要 jekyll-algolia，可以取消注释：
# gem "jekyll-algolia"

# 注意：如果使用 GitHub Actions 自定义构建，并且你的 _config.yml 中有 `plugins:` 列表，
# 那么你需要确保所有列出的插件都在 Gemfile 中。
