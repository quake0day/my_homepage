# 运维手册 — darlingtree.com

> 给未来自己看的速查表。如果忘了怎么操作,从这里查起。

## 一眼看懂的架构

```
┌─ Mac (~/my_homepage) ────────┐     ┌─ GitHub quake0day/my_homepage ─┐
│  pnpm dev / pnpm run         │────►│  main 分支 = 唯一真相         │
│  publish:cf (手动部署)       │     │  static assets ~106MB          │
└──────────────────────────────┘     └────────────────────────────────┘
                                            ▲
            ┌───────────────────────────────┘
            │ git push(每周日 03:00 UTC,只改 publications.json)
┌─ PVE LXC 181 (192.168.68.61) ─┐
│  cron_update.sh               │
│  Scholar 抓 → Kimi K2.6 解析  │
└────────────────────────────────┘

┌─ Cloudflare ────────────────────────────────────────────────────────┐
│  Pages "my-homepage" ←── wrangler pages deploy dist                 │
│  ├─ darlingtree.com (active, Google cert)                           │
│  └─ www.darlingtree.com                                             │
│                                                                      │
│  R2 "darlingtree-assets" ──► pub-1c5db851...r2.dev/{files,slides}   │
│                                                                      │
│  Workers AI: @cf/moonshotai/kimi-k2.6 (LXC 调用)                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 日常任务速查

### 📝 加 / 改一篇论文

编辑 `src/data/publications.json`,追加一条:

```json
{
  "id": 100,
  "type": 1,
  "title": "Your Paper Title",
  "author": "Amay Jain, Liu Cui, Si Chen",
  "confname": "ACM MobiCom 2027",
  "urlpaper": "https://dl.acm.org/...",
  "urlslides": "/static/slides/mobicom27.pdf",
  "urlpdf": "https://arxiv.org/abs/xxxx.yyyyy",
  "urlcite": "",
  "video": "",
  "urlaward": "",
  "text": "",
  "cite": 0,
  "place": "San Diego, CA, Nov 2027",
  "year": 2027,
  "cluster": "",
  "hidden": 0
}
```

**字段说明:**
- `type`: 1=Conference, 2=Journal, 3=Preprint, 4=Book Chapter
- `id`: 递增,别跟现有重
- `text`: 非空则显示一个奖项/备注 badge(如 `"🏆 Best Paper Award"`)
- `urlaward`: 有的话 badge 变成可点的链接
- `hidden`: 1 = 默认不显示(勾 "Show All" 才看到),0 = 显示

本地验证 + 部署:

```fish
cd ~/my_homepage
pnpm dev                  # http://localhost:4321 本地预览
pnpm run publish:cf       # build + deploy(约 1 分钟)
git add -A && git commit -m "add MobiCom 2027" && git push
```

### ✏️ 改个人介绍 / 奖项 / 课程

这些都**硬编码在 `src/pages/index.astro`** 里(不在 JSON)。常改的区域:

| 想改 | 找这个段 |
|---|---|
| 头像旁的联系方式、头衔 | `<!-- ===== HERO / PROFILE ===== -->` |
| 研究介绍段落 | `<!-- ===== ABOUT ===== -->` |
| "Research featured in" logos | frontmatter 里的 `const media = [...]` |
| Media Appearances | `<!-- ===== MEDIA APPEARANCES ===== -->` |
| Invited Talks | `<!-- ===== INVITED TALKS ===== -->` |
| 奖项列表 | frontmatter 里的 `const awards = [...]` |
| Services(Professional / University) | `<!-- ===== SERVICES ===== -->` |
| Teaching 课程学期 tag | frontmatter 里的 `softwareSecurityYears` / `malwareYears` |
| Sabbatical 状态 | `<!-- ===== TEACHING ===== -->` 里的灰框 |

改完 → `pnpm run publish:cf`。

### 📤 上传大文件(>24MB)

CF Pages 单文件限 25 MiB,所以大于 24MB 的文件**走 R2**。

```fish
cd ~/my_homepage
# 放进 git(保留备份)
cp ~/Downloads/HugeBrochure.pdf public/static/files/

# 同时上传到 R2(公开访问)
npx wrangler r2 object put "darlingtree-assets/files/HugeBrochure.pdf" \
  --file=public/static/files/HugeBrochure.pdf \
  --content-type=application/pdf --remote

# 页面里引用 R2 URL(不要用 /static/files/... 因为 deploy 时会被剔除):
# https://pub-1c5db85189b141deba911473ca303106.r2.dev/files/HugeBrochure.pdf
```

部署脚本 `publish:cf` 会自动把 `dist/` 里 >24MB 的文件删掉再推 Pages,所以 **放在 `public/static/` 里是安全的**,只是不会出现在在线站上(R2 里有)。

### 🔄 手动跑一次 citation 更新(立即)

```fish
ssh root@192.168.68.61 /root/my_homepage/scripts/cron_update.sh
```

输出会直接显示。有改动会自动 `git push`。push 完**要手动部署**(见下):

```fish
cd ~/my_homepage && git pull && pnpm run publish:cf
```

### 🔍 看上次 cron 跑了啥

```fish
ssh root@192.168.68.61 'tail -n 80 /var/log/citation-bot.log'
```

---

## 部署

### 标准部署(从 Mac)

```fish
cd ~/my_homepage
pnpm run publish:cf
```

这条命令会:
1. `pnpm build` → 生成 `dist/`
2. `find dist -type f -size +24M -print -delete` → 剔掉 CF Pages 单文件超限的文件
3. `wrangler pages deploy dist --project-name=my-homepage --branch=main`

成功输出类似:

```
✨ Success! Uploaded 124 files (36.93 sec)
✨ Deployment complete! Take a peek over at https://xxxxxxxx.my-homepage-586.pages.dev
```

正式域名生效在 1-2 分钟后,先去 preview URL 看渲染对不对。

### 本地预览(不部署)

```fish
pnpm dev      # 改代码热更新,http://localhost:4321
pnpm build    # 产物在 dist/
pnpm preview  # 预览构建产物
```

### 部署失败常见原因

| 错误 | 处理 |
|---|---|
| `Pages only supports files up to 25 MiB` | 有新大文件混进 `public/`,要么缩小,要么上 R2 并在 index.astro 里引用 R2 URL |
| `Authentication error` | wrangler OAuth 过期,跑一次 `npx wrangler login` |
| build 卡死 | 清 `rm -rf dist .astro node_modules && pnpm install && pnpm build` |

---

## Citation 自动更新机制

### 它怎么工作

1. **每周日 03:00 UTC**,LXC 181 的 cron 运行 `/root/my_homepage/scripts/cron_update.sh`
2. 脚本先 `git pull` 保证本地是最新
3. 调 `scripts/update_citations.py`:
   - 抓 Google Scholar profile `DDLTYpAAAAAJ` 的前 9 页(最多 200 篇)
   - 预解析出 `title ||| cite_count` 行
   - 丢给 Cloudflare Workers AI 的 Kimi K2.6 清洗标题
   - 用字符串相似度匹配到 `publications.json` 里的 `id`
   - 只改 `cite` 字段,其他不动
4. 如果有 diff,`git commit` + `git push`
5. **CF Pages 不会自动重建**,需要 Mac 上 `pnpm run publish:cf`(见下方 "唯一的小遗留")

### 看状态

```fish
# 最近日志
ssh root@192.168.68.61 'tail -n 80 /var/log/citation-bot.log'

# cron 本身是否还在
ssh root@192.168.68.61 'crontab -l'

# LXC 是否还活着
curl -sk "https://192.168.68.56:8006/api2/json/nodes/quake0day/lxc/181/status/current" \
  -H "Authorization: PVEAPIToken=root@pam!new2=ede4986a-4eee-4270-8081-36ba4b112ce3"
```

### 手动重跑

```fish
ssh root@192.168.68.61 /root/my_homepage/scripts/cron_update.sh
```

### 为什么不用 GitHub Actions

Scholar 会 403 封 Azure 数据中心 IP。GH Actions 跑出来永远失败。`.github/workflows/update-citations.yml` 保留着但只支持 `workflow_dispatch`(手动),schedule 触发已去掉。

---

## LXC 181(citation-bot)运维

**身份:** 192.168.68.61,Debian 12,1 vCPU / 512M / 4G,hostname `citation-bot`
**SSH:** `ssh root@192.168.68.61`(你的 `~/.ssh/id_ed25519.pub` 已授权)

### 常用操作

```fish
# 进 shell
ssh root@192.168.68.61

# 重启
curl -sk -X POST "https://192.168.68.56:8006/api2/json/nodes/quake0day/lxc/181/status/reboot" \
  -H "Authorization: PVEAPIToken=root@pam!new2=ede4986a-4eee-4270-8081-36ba4b112ce3"

# 停 / 启
# 把 reboot 换成 stop / start

# 更新 CF API token(比如轮换后)
ssh root@192.168.68.61 'nano /root/my_homepage/.env'

# 同步最新代码(脚本改动后)
# cron_update.sh 每次跑都会自动 git pull,一般不用手动
ssh root@192.168.68.61 'cd /root/my_homepage && git pull'
```

### LXC 磁盘满了怎么办

4GB 应该永远用不完(clone 占 1.1G)。如果满了:

```fish
ssh root@192.168.68.61 'du -sh /var/log/* /root/my_homepage/.git | sort -h'
# 通常是 /var/log/citation-bot.log 太大 → 截断或 logrotate
ssh root@192.168.68.61 'truncate -s 0 /var/log/citation-bot.log'
```

---

## 密钥 / Token 台账

| Token | 作用 | 存哪 | 怎么轮换 |
|---|---|---|---|
| GitHub deploy key `citation-bot (pve-lxc-181)` | LXC push 权限 | GH repo Deploy Keys + LXC `/root/.ssh/github_deploy` | GH 侧删旧 + LXC 里 `ssh-keygen` + `gh repo deploy-key add` |
| CF API token `cfut_VdzO8...` (Workers AI Read) | LXC 和 GH Actions 调 Kimi | LXC `/root/my_homepage/.env` + GH secret `CLOUDFLARE_API_TOKEN` | CF dashboard 创建新的 → 更新两处 |
| Wrangler OAuth(Mac) | `pnpm run publish:cf` 部署 Pages | `~/Library/Preferences/.wrangler/config/default.toml` | 过期后 `npx wrangler login` 重新授权 |
| PVE API token `root@pam!new2` | 管理 LXC 生命周期 | 你的密码管理器 | PVE GUI 里删旧建新 |

**⚠️ 都不要提交到 git。** repo 里的 `.gitignore` 已经排除 `.env`,但每次加新敏感文件前扫一眼 `git status` 再说。

---

## 故障排查

### 站打不开

```fish
# 1. DNS 对不对
dig +short darlingtree.com @1.1.1.1
# 应该是 172.66.x.x 或类似 CF 边缘 IP

# 2. CF Pages 部署是不是挂了
npx wrangler pages deployment list --project-name=my-homepage | head -5

# 3. 自己站的 HTTP 状态
curl -sI https://darlingtree.com/ | head -3
```

### `pnpm run publish:cf` 失败

看上方 "部署失败常见原因" 表。

### Scholar 抓不到 / citation bot 日志全是 403

可能 Scholar 对你家 IP 也开始下手了(极少见)。临时方案:

```fish
# 在 LXC 里改用 curl 走住家 VPN 或代理
# 或者直接不跑自动,手动维护 JSON 里的 cite 字段
```

长期:把抓取改成 Semantic Scholar API + author disambiguation(比较折腾,先不搞)。

### Kimi K2.6 返 null content

通常是 `max_tokens` 不够(模型先推理吃 tokens 再输出)。现在设的 8192 够 50 篇以内论文用。再涨就改 `scripts/update_citations.py` 里的 `call_ai(prompt, max_tokens=8192)`。

### 部署成功但内容没变

CF Pages 有边缘缓存,偶尔需要等 1-2 分钟。hard refresh(⌘⇧R)或开无痕。还不行:

```fish
# 查最新 deployment 是不是刚才那次
npx wrangler pages deployment list --project-name=my-homepage | head -3
```

---

## 唯一的小遗留

**CF Pages 项目是 Direct Upload 模式,不监听 GitHub push。**

所以 LXC 周更 `publications.json` 推到 GH 之后,线上站还是旧数据,**必须人工去 Mac 上跑一次 `pnpm run publish:cf` 才能反映到外网**。

想修掉这个遗留,两条路:

1. **改 Git 集成**:dashboard → Pages → my-homepage → Settings → Builds & deployments → Connect to Git。之后每次 push 自动 rebuild。**推荐**,一次性操作。
2. **LXC 也负责部署**:装 Node+pnpm+wrangler,新建一个带 `Pages:Edit` scope 的 CF token 放 `.env`,在 `cron_update.sh` 最后加 `pnpm run publish:cf`。复杂度更高。

我默认你能接受"每周手动点一下部署"(citation 变动频率很低)。如果想自动化任何一条,告诉我。

---

## 老服务器清理(未完成)

旧 Linode `172.104.211.70` 还在跑 Apache+Flask,每月 $6。等观察新站 2 周无异常后:

```fish
sshpass -p '@Lara4chensi' ssh root@172.104.211.70 'sudo systemctl stop apache2 && sudo systemctl disable apache2'
# 再过一周去 Linode 控制台关掉这台机器
```

同时去 https://console.anthropic.com/settings/keys 把旧的 Anthropic API key 作废(现在已经完全不用了,老 cron 也随 Linode 关一起消失)。
