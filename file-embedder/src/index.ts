/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */


type SlotStatus = 'pending' | 'ready';

type SlotRecord = {
	id: string;
	status: SlotStatus;
	key: string; // R2 object key
	size?: number; // bytes
	contentType?: string;
	fileName?: string;
	createdAt: string; // ISO
	uploadedAt?: string; // ISO
};

const KV_KEYS = {
	usage: 'usage:total',
	slot: (id: string) => `slot:${id}`,
} as const;

function json(res: unknown, init: ResponseInit = {}): Response {
	return Response.json(res, { headers: { 'content-type': 'application/json' }, ...init });
}

function unauthorized(): Response {
	return new Response('Unauthorized', { status: 401, headers: { 'www-authenticate': 'Bearer' } });
}

function getBearerToken(req: Request): string | null {
	const h = req.headers.get('authorization');
	if (!h) return null;
	const [scheme, token] = h.split(' ');
	if (!scheme || scheme.toLowerCase() !== 'bearer') return null;
	return token || null;
}

async function getUsage(env: Env): Promise<number> {
	const v = await env.fileembedkv.get(KV_KEYS.usage, 'text');
	return v ? Number(v) : 0;
}

async function setUsage(env: Env, bytes: number): Promise<void> {
	await env.fileembedkv.put(KV_KEYS.usage, String(bytes));
}

async function getSlot(env: Env, id: string): Promise<SlotRecord | null> {
	return await env.fileembedkv.get<SlotRecord>(KV_KEYS.slot(id), 'json');
}

async function putSlot(env: Env, rec: SlotRecord): Promise<void> {
	await env.fileembedkv.put(KV_KEYS.slot(rec.id), JSON.stringify(rec));
}

function html(body: string, init?: ResponseInit): Response {
	return new Response(body, {
		headers: {
			'content-type': 'text/html; charset=utf-8',
		},
		...init,
	});
}

function uiPage(id: string, remainingBytes: number): Response {
	const remainingMB = Math.floor(remainingBytes / (1024 * 1024));
	const page = `<!doctype html>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Upload file</title>
<style>
	body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
	.box { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; max-width: 560px; }
	input[type=file] { margin: 0.5rem 0 1rem; }
	progress { width: 100%; height: 12px; }
	.muted { color: #666; font-size: 0.9rem; }
	button { padding: 0.6rem 1rem; border-radius: 6px; border: 1px solid #ccc; background: #f7f7f7; cursor: pointer; }
	button:disabled { opacity: 0.7; cursor: not-allowed; }
	#msg { margin-top: 0.75rem; }
	code { background: #f2f2f2; padding: 2px 4px; border-radius: 4px; }
	.row { display: flex; gap: .5rem; align-items: center; }
	a { color: #06c; }
	.hidden { display: none; }
	.ok { color: #176b1b; }
	.err { color: #a40000; }
	.center { text-align:center }
	.pill { display:inline-block; padding:.2rem .5rem; border-radius:999px; background:#eef; color:#224; font-size:.8rem }
	.mt { margin-top: .75rem; }
	.mb { margin-bottom: .75rem; }
	.drag { padding: 1rem; border: 2px dashed #bbb; border-radius: 8px; text-align:center; color:#555 }
	.drag.hover { background: #fafafa; border-color: #888 }
	small { color: #555 }
</style>
<div class="box">
	<h2>Upload a file</h2>
	<p class="muted">This link accepts one file. Once uploaded, visiting <code>/storage/${id}</code> will return the file.</p>
	<div id="drop" class="drag mb">Drop a file here or choose below</div>
	<input id="file" type="file" />
	<button id="upload" disabled>Upload</button>
	<div id="msg" class="muted">Remaining capacity: <b>${remainingMB} MB</b></div>
	<p class="muted mt">Keep this tab open until the upload completes. Files larger than the remaining capacity will be rejected.</p>
</div>
<script>
	const fileInput = document.getElementById('file');
	const btn = document.getElementById('upload');
	const prog = document.getElementById('prog');
	const msg = document.getElementById('msg');
	const drop = document.getElementById('drop');

	let picked;
	function setPicked(f){ picked = f; btn.disabled = !picked; }
	fileInput.addEventListener('change', () => setPicked(fileInput.files?.[0]));

	;['dragenter','dragover'].forEach(ev => drop.addEventListener(ev, e=>{ e.preventDefault(); drop.classList.add('hover'); }));
	;['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e=>{ e.preventDefault(); drop.classList.remove('hover'); }));
	drop.addEventListener('drop', e => { const f = e.dataTransfer?.files?.[0]; if(f){ setPicked(f); } });

	async function upload() {
		if (!picked) return;
		btn.disabled = true;
		msg.textContent = 'Uploading…';
		try {
			// Use fetch with the Blob body; browser sets a fixed Content-Length.
			const res = await fetch(location.pathname, {
				method: 'POST',
				headers: {
					'content-type': picked.type || 'application/octet-stream',
					'x-file-name': encodeURIComponent(picked.name)
				},
				body: picked,
				// Avoid bfcache for huge uploads.
				cache: 'no-store',
			});
			if (res.ok) {
				msg.innerHTML = '<span class="ok">Upload complete. Redirecting…</span>';
				setTimeout(()=> location.reload(), 400);
			} else {
				const t = await res.text();
				msg.innerHTML = '<span class="err">Upload failed: ' + res.status + ' ' + t + '</span>';
				btn.disabled = false;
			}
		} catch (e) {
			msg.innerHTML = '<span class="err">' + e + '</span>';
			btn.disabled = false;
		}
	}
	btn.addEventListener('click', upload);
</script>`;
	return html(page);
}

function formatBytes(n: number): string {
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	let i = 0; let v = n;
	while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
	return `${v.toFixed(2)} ${units[i]}`;
}

export default {
	async fetch(request, env): Promise<Response> {
		const url = new URL(request.url);
		const { pathname } = url;
		const BYTES_MAX_CAP = Number(env.MAX_CAP) * 1024 * 1024 * 1024;

		// POST /api/new-id -> { id, url }
		if (pathname === '/api/new-id' && request.method === 'POST') {
			const token = getBearerToken(request);
			if (!token || token !== env.SECRET_TOKEN) return unauthorized();
			const id = crypto.randomUUID();
			const rec: SlotRecord = {
				id,
				status: 'pending',
				key: `files/${id}`,
				createdAt: new Date().toISOString(),
			};
			await putSlot(env, rec);
			return json({ id, url: `/storage/${id}` }, { status: 201 });
		}

		// /storage/:id
		const m = pathname.match(/^\/storage\/([a-f0-9\-]{16,})$/i);
		if (m) {
			const id = m[1];
			const rec = await getSlot(env, id);
			if (!rec) {
				return new Response('Not found', { status: 404 });
			}

			// DELETE to remove file (auth required)
			if (request.method === 'DELETE') {
				const token = getBearerToken(request);
				if (!token || token !== env.SECRET_TOKEN) return unauthorized();
				if (rec.status === 'ready' && rec.size && rec.key) {
					await env.fileembeds.delete(rec.key);
					// decrement usage
					const current = await getUsage(env);
					const next = Math.max(0, current - (rec.size || 0));
					await setUsage(env, next);
					// delete kv entry
					await env.fileembedkv.delete(KV_KEYS.slot(id));
				}
				return new Response(null, { status: 204 });
			}

			if (request.method === 'POST') {
				if (rec.status === 'ready') return new Response('Already uploaded', { status: 409 });
				const lenHeader = request.headers.get('content-length');
				if (!lenHeader) return new Response('Content-Length required', { status: 411 });
				const contentLength = Number(lenHeader);
				if (!Number.isFinite(contentLength) || contentLength < 0) return new Response('Invalid Content-Length', { status: 400 });

				const current = await getUsage(env);
				const remaining = BYTES_MAX_CAP - current;
				if (contentLength > remaining) {
					return new Response(`Insufficient Storage. Remaining ${formatBytes(remaining)} but upload is ${formatBytes(contentLength)}.`, { status: 507 });
				}

				const body = request.body ? request.body.pipeThrough(new FixedLengthStream(contentLength)) : null;
				const contentType = request.headers.get('content-type') || 'application/octet-stream';
				const rawName = request.headers.get('x-file-name') || '';
				const fileName = rawName ? decodeURIComponent(rawName) : undefined;

				// Perform the upload to R2
				const putResult = await env.fileembeds.put(rec.key, body!, {
					httpMetadata: { contentType, contentDisposition: fileName ? `inline; filename*=UTF-8''${encodeURIComponent(fileName)}` : undefined },
				});

				// Update usage and slot metadata
				const nextUsage = current + contentLength;
				await setUsage(env, nextUsage);
				const updated: SlotRecord = {
					...rec,
					status: 'ready',
					size: contentLength,
					contentType,
					fileName,
					uploadedAt: new Date().toISOString(),
				};
				await putSlot(env, updated);

				return json({ ok: true, etag: putResult?.etag ?? undefined }, { status: 201 });
			}

			// GET: if ready -> file, else -> show upload UI
			if (request.method === 'GET') {
				if (rec.status === 'ready') {
					const obj = await env.fileembeds.get(rec.key);
					if (!obj) return new Response('Not found', { status: 404 });
					const h = new Headers();
					obj.writeHttpMetadata(h);
					if (rec.fileName) h.set('content-disposition', `inline; filename*=UTF-8''${encodeURIComponent(rec.fileName)}`);
					h.set('etag', obj.httpEtag);
					h.set('accept-ranges', 'bytes');
					h.set('cache-control', 'private, max-age=0, must-revalidate');
					// Let R2 provide content-length and partial content status via range
					return new Response(obj.body, { status: 200, headers: h });
				}
				const remaining = BYTES_MAX_CAP - (await getUsage(env));
				return uiPage(id, Math.max(0, remaining));
			}

			return new Response('Method Not Allowed', { status: 405 });
		}

		// Root/help
		if (pathname === '/' && request.method === 'GET') {
			return html(`<!doctype html><meta charset="utf-8" /><title>file-embedder</title>
			<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem;max-width:720px} code{background:#f2f2f2;padding:2px 4px;border-radius:4px}</style>
			<h2>File Embedder</h2>`);
		}

		return new Response('Not found', { status: 404 });
	},
} satisfies ExportedHandler<Env>;
