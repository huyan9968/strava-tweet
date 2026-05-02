/**
 * Strava Webhook → GitHub 自动创建 PR
 *
 * 环境变量（在 Cloudflare 后台设置）：
 *   STRAVA_VERIFY_TOKEN   自定义验证字符串，注册 Webhook 时用
 *   STRAVA_CLIENT_ID      Strava App client_id
 *   STRAVA_CLIENT_SECRET  Strava App client_secret
 *   STRAVA_REFRESH_TOKEN  长期有效的 refresh_token
 *   GITHUB_TOKEN          GitHub PAT，需要 repo + pull_requests 权限
 */

const GITHUB_REPO = 'huyan9968/strava-tweet';
const GITHUB_BASE_BRANCH = 'main';

// 固定的验证 token
const STRAVA_VERIFY_TOKEN = 'my-strava-webhook-2024';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── GET：Strava 注册 Webhook 时的验证请求 ──────────
    if (request.method === 'GET') {
      const mode = url.searchParams.get('hub.mode');
      const challenge = url.searchParams.get('hub.challenge');
      const token = url.searchParams.get('hub.verify_token');

      if (mode === 'subscribe' && token === STRAVA_VERIFY_TOKEN) {
        return Response.json({ 'hub.challenge': challenge });
      }
      return new Response('Forbidden', { status: 403 });
    }

    // ── POST：Strava 推送新活动通知 ───────────────────
    if (request.method === 'POST') {
      let body;
      try {
        body = await request.json();
      } catch {
        return new Response('Bad Request', { status: 400 });
      }

      if (body.object_type === 'activity' && body.aspect_type === 'create') {
        try {
          const accessToken = await getStravaAccessToken(env);
          const activity = await fetchStravaActivity(body.object_id, accessToken);
          await createRunPR(activity, env);
        } catch (err) {
          return new Response(`Error: ${err.message}`, { status: 502 });
        }
      }

      return new Response('OK');
    }

    return new Response('Not Found', { status: 404 });
  },
};

// ── Strava helpers ────────────────────────────────────────

async function getStravaAccessToken(env) {
  const resp = await fetch('https://www.strava.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: env.STRAVA_CLIENT_ID,
      client_secret: env.STRAVA_CLIENT_SECRET,
      refresh_token: env.STRAVA_REFRESH_TOKEN,
      grant_type: 'refresh_token',
    }),
  });
  if (!resp.ok) throw new Error(`Strava token refresh failed: ${await resp.text()}`);
  const data = await resp.json();
  return data.access_token;
}

async function fetchStravaActivity(activityId, accessToken) {
  const resp = await fetch(`https://www.strava.com/api/v3/activities/${activityId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!resp.ok) throw new Error(`Strava API failed: ${await resp.text()}`);
  return resp.json();
}

// ── Markdown 生成 ─────────────────────────────────────────

function formatActivityMarkdown(activity) {
  const date = activity.start_date_local.slice(0, 10);
  const distanceKm = (activity.distance / 1000).toFixed(2);
  const durationMin = Math.floor(activity.moving_time / 60);
  const paceSec = activity.moving_time / (activity.distance / 1000);
  const paceMin = Math.floor(paceSec / 60);
  const paceFmt = `${paceMin}'${Math.round(paceSec % 60).toString().padStart(2, '0')}"`;
  const elevGain = activity.total_elevation_gain.toFixed(0);
  const avgHr = activity.average_heartrate
    ? `${Math.round(activity.average_heartrate)} bpm`
    : 'N/A';

  return `# ${activity.name}

**日期**: ${date}
**类型**: ${activity.sport_type}

## 数据

| 项目 | 数值 |
|------|------|
| 距离 | ${distanceKm} km |
| 时长 | ${durationMin} 分钟 |
| 配速 | ${paceFmt}/km |
| 爬升 | ${elevGain} m |
| 平均心率 | ${avgHr} |

## 备注

${activity.description || '无'}

---
*自动生成 · [Strava 活动链接](https://www.strava.com/activities/${activity.id})*
`;
}

// ── GitHub helpers ────────────────────────────────────────

async function githubRequest(path, method, body, token) {
  const resp = await fetch(`https://api.github.com/repos/${GITHUB_REPO}${path}`, {
    method,
    headers: {
      Authorization: `token ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'strava-webhook-worker',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await resp.text();
  if (!resp.ok) throw new Error(`GitHub ${method} ${path} failed: ${text}`);
  return JSON.parse(text);
}

async function createRunPR(activity, env) {
  const token = env.GITHUB_TOKEN;
  const date = activity.start_date_local.slice(0, 10);
  const distanceKm = (activity.distance / 1000).toFixed(1);
  const branch = `run/activity-${activity.id}`;
  const filePath = `runs/${date}-${activity.id}.md`;

  // 获取 main 分支最新 SHA
  const ref = await githubRequest(`/git/ref/heads/${GITHUB_BASE_BRANCH}`, 'GET', null, token);
  const baseSha = ref.object.sha;

  // 创建新分支
  await githubRequest('/git/refs', 'POST', {
    ref: `refs/heads/${branch}`,
    sha: baseSha,
  }, token);

  // 在新分支写入 Markdown 文件（btoa 处理中文需先转 UTF-8 字节）
  const content = btoa(unescape(encodeURIComponent(formatActivityMarkdown(activity))));
  await githubRequest(`/contents/${filePath}`, 'PUT', {
    message: `run: ${date} ${distanceKm}km - ${activity.name}`,
    content,
    branch,
  }, token);

  // 开 PR
  await githubRequest('/pulls', 'POST', {
    title: `🏃 ${date} · ${distanceKm}km · ${activity.name}`,
    body: [
      `Strava 活动自动同步`,
      ``,
      `| 项目 | 值 |`,
      `|------|----|`,
      `| 活动 ID | ${activity.id} |`,
      `| 距离 | ${distanceKm} km |`,
      `| 运动类型 | ${activity.sport_type} |`,
      ``,
      `[查看 Strava 原始活动](https://www.strava.com/activities/${activity.id})`,
    ].join('\n'),
    head: branch,
    base: GITHUB_BASE_BRANCH,
  }, token);
}

// ── Markdown 生成 ─────────────────────────────────────────

function formatActivityMarkdown(activity) {
  const date        = activity.start_date_local.slice(0, 10);
  const distanceKm  = (activity.distance / 1000).toFixed(2);
  const durationMin = Math.floor(activity.moving_time / 60);
  const paceSec     = activity.moving_time / (activity.distance / 1000);
  const paceMin     = Math.floor(paceSec / 60);
  const paceFmt     = `${paceMin}'${Math.round(paceSec % 60).toString().padStart(2, '0')}"`;
  const elevGain    = activity.total_elevation_gain.toFixed(0);
  const avgHr       = activity.average_heartrate
    ? `${Math.round(activity.average_heartrate)} bpm`
    : 'N/A';

  return `# ${activity.name}

**日期**: ${date}
**类型**: ${activity.sport_type}

## 数据

| 项目 | 数值 |
|------|------|
| 距离 | ${distanceKm} km |
| 时长 | ${durationMin} 分钟 |
| 配速 | ${paceFmt}/km |
| 爬升 | ${elevGain} m |
| 平均心率 | ${avgHr} |

## 备注

${activity.description || '无'}

---
*自动生成 · [Strava 活动链接](https://www.strava.com/activities/${activity.id})*
`;
}

// ── GitHub helpers ────────────────────────────────────────

async function githubRequest(path, method, body, token) {
  const resp = await fetch(`https://api.github.com/repos/${GITHUB_REPO}${path}`, {
    method,
    headers: {
      Authorization:  `token ${token}`,
      Accept:         'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent':   'strava-webhook-worker',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await resp.text();
  if (!resp.ok) throw new Error(`GitHub ${method} ${path} failed: ${text}`);
  return JSON.parse(text);
}

async function createRunPR(activity, env) {
  const token      = env.GITHUB_TOKEN;
  const date       = activity.start_date_local.slice(0, 10);
  const distanceKm = (activity.distance / 1000).toFixed(1);
  const branch     = `run/activity-${activity.id}`;
  const filePath   = `runs/${date}-${activity.id}.md`;

  // 获取 main 分支最新 SHA
  const ref     = await githubRequest(`/git/ref/heads/${GITHUB_BASE_BRANCH}`, 'GET', null, token);
  const baseSha = ref.object.sha;

  // 创建新分支
  await githubRequest('/git/refs', 'POST', {
    ref: `refs/heads/${branch}`,
    sha: baseSha,
  }, token);

  // 在新分支写入 Markdown 文件（btoa 处理中文需先转 UTF-8 字节）
  const content = btoa(unescape(encodeURIComponent(formatActivityMarkdown(activity))));
  await githubRequest(`/contents/${filePath}`, 'PUT', {
    message: `run: ${date} ${distanceKm}km - ${activity.name}`,
    content,
    branch,
  }, token);

  // 开 PR
  await githubRequest('/pulls', 'POST', {
    title: `🏃 ${date} · ${distanceKm}km · ${activity.name}`,
    body: [
      `Strava 活动自动同步`,
      ``,
      `| 项目 | 值 |`,
      `|------|----|`,
      `| 活动 ID | ${activity.id} |`,
      `| 距离 | ${distanceKm} km |`,
      `| 运动类型 | ${activity.sport_type} |`,
      ``,
      `[查看 Strava 原始活动](https://www.strava.com/activities/${activity.id})`,
    ].join('\n'),
    head:  branch,
    base:  GITHUB_BASE_BRANCH,
  }, token);
}
