/**
 * Strava Webhook → GitHub Actions 触发器
 *
 * 环境变量（在 Cloudflare Workers 后台 Settings → Variables 设置）：
 *   STRAVA_VERIFY_TOKEN   自定义验证字符串，与 Strava Webhook 注册时一致
 *   GITHUB_TOKEN          GitHub PAT，需要 repo 权限（用于触发 repository_dispatch）
 *
 * 不再需要 STRAVA_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN
 * （Strava 数据获取已移至 GitHub Actions 中的 strava_tweet.py）
 */

const GITHUB_REPO = 'huyan9968/strava-tweet';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── GET：Strava 注册 Webhook 时的验证请求 ──────────────────────────
    if (request.method === 'GET') {
      const mode      = url.searchParams.get('hub.mode');
      const challenge = url.searchParams.get('hub.challenge');
      const token     = url.searchParams.get('hub.verify_token');

      if (mode === 'subscribe' && token === env.STRAVA_VERIFY_TOKEN) {
        return Response.json({ 'hub.challenge': challenge });
      }
      return new Response('Forbidden', { status: 403 });
    }

    // ── POST：Strava 推送新活动通知 ────────────────────────────────────
    if (request.method === 'POST') {
      let body;
      try {
        body = await request.json();
      } catch {
        return new Response('Bad Request', { status: 400 });
      }

      // 只处理新建跑步活动
      if (body.object_type === 'activity' && body.aspect_type === 'create') {
        try {
          await triggerGitHubActions(body.object_id, env);
        } catch (err) {
          console.error('触发 GitHub Actions 失败:', err.message);
          // 仍然返回 200，避免 Strava 反复重试
        }
      }

      return new Response('OK');
    }

    return new Response('Not Found', { status: 404 });
  },
};

/**
 * 向 GitHub 发送 repository_dispatch 事件，触发 strava_tweet.yml 和 build_site.yml
 */
async function triggerGitHubActions(activityId, env) {
  const resp = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/dispatches`, {
    method: 'POST',
    headers: {
      Authorization:  `token ${env.GITHUB_TOKEN}`,
      Accept:         'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent':   'strava-webhook-worker',
    },
    body: JSON.stringify({
      event_type:     'strava_activity',
      client_payload: { activity_id: activityId },
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`GitHub dispatch 失败 (${resp.status}): ${text}`);
  }
}
