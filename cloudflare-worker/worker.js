/**
 * Strava Webhook → GitHub Actions 触发器
 *
 * 环境变量（在 Cloudflare 后台设置）：
 *   STRAVA_VERIFY_TOKEN  自定义验证字符串，注册 Webhook 时用
 *   GITHUB_TOKEN         GitHub PAT，需要 repo 权限
 */

const GITHUB_REPO = 'huyan9968/strava-tweet';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── GET：Strava 注册 Webhook 时的验证请求 ──────────
    if (request.method === 'GET') {
      const mode      = url.searchParams.get('hub.mode');
      const challenge = url.searchParams.get('hub.challenge');
      const token     = url.searchParams.get('hub.verify_token');

      if (mode === 'subscribe' && token === env.STRAVA_VERIFY_TOKEN) {
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

      // 只处理新活动创建事件
      if (body.object_type === 'activity' && body.aspect_type === 'create') {
        const resp = await fetch(
          `https://api.github.com/repos/${GITHUB_REPO}/dispatches`,
          {
            method: 'POST',
            headers: {
              Authorization:  `token ${env.GITHUB_TOKEN}`,
              Accept:         'application/vnd.github.v3+json',
              'Content-Type': 'application/json',
              'User-Agent':   'strava-webhook-worker',
            },
            body: JSON.stringify({ event_type: 'strava_activity' }),
          }
        );

        if (!resp.ok) {
          const text = await resp.text();
          return new Response(`GitHub trigger failed: ${text}`, { status: 502 });
        }
      }

      return new Response('OK');
    }

    return new Response('Not Found', { status: 404 });
  },
};
