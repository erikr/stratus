# Stratus Eye Jekyll Site

Faithful static recreation of the downloaded `stratuseye.com` Webflow site for GitHub Pages.

## Local Development

```sh
bundle install
bundle exec jekyll serve
```

With Ruby 3.4, `csv` and `logger` are declared explicitly in the Gemfile because Jekyll 4 loads them as runtime libraries.

The source HTML snapshots live outside the repo at `/Users/erik/Downloads/stratuseye.com`.
To regenerate the converted pages and vendored assets:

```sh
python3 tools/rebuild_from_download.py
```
