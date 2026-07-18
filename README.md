name: 更新热榜数据
on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - name: 生成页面
        run: python3 generate.py
      - name: 上传HTML
        uses: actions/upload-pages-artifact@v2
        with:
          path: .
  deploy:
    needs: update
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    steps:
      - uses: actions/deploy-pages@v2
