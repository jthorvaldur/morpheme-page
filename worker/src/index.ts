export interface Env {
  DB: D1Database;
  RATE_LIMIT: KVNamespace;
  ENVIRONMENT: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ALLOWED_ORIGINS = [
  'https://morpheme.page',
  'https://www.morpheme.page',
  'http://localhost:3000',
];

function corsHeaders(request: Request): Record<string, string> {
  const origin = request.headers.get('Origin') || '';
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

function jsonResponse(data: unknown, status = 200, request?: Request): Response {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (request) {
    Object.assign(headers, corsHeaders(request));
  }
  return new Response(JSON.stringify(data), { status, headers });
}

function errorResponse(message: string, status = 400, request?: Request): Response {
  return jsonResponse({ error: message }, status, request);
}

// ---------------------------------------------------------------------------
// Rate limiting (stub)
// ---------------------------------------------------------------------------

// TODO: Implement sliding-window rate limiting using KV
// Key format: `rate:{ip}:{endpoint}` with TTL-based expiry
async function checkRateLimit(
  _kv: KVNamespace,
  _ip: string,
  _endpoint: string,
): Promise<{ allowed: boolean; remaining: number }> {
  // Stub: always allow for now
  return { allowed: true, remaining: 100 };
}

// ---------------------------------------------------------------------------
// Route handlers
// ---------------------------------------------------------------------------

/**
 * POST /api/ask
 * AI-powered Q&A about word decompositions and morphological analysis.
 */
async function handleAsk(request: Request, _env: Env): Promise<Response> {
  const body = await request.json<{ question?: string }>();
  if (!body.question || typeof body.question !== 'string') {
    return errorResponse('Missing required field: question', 400, request);
  }

  // TODO: Call Claude Haiku via Anthropic API
  // - Build system prompt from knowledge/ markdown files
  // - Include relevant decompositions from D1 as context
  // - Stream or return the response

  const mockAnswer =
    'This is a stub response. The AI Q&A endpoint will use Claude Haiku ' +
    'to answer questions about morphological decomposition, the VCC negation ' +
    'pattern, and authority language analysis.';

  return jsonResponse(
    {
      question: body.question,
      answer: mockAnswer,
      sources: [],
      model: 'stub',
    },
    200,
    request,
  );
}

/**
 * POST /api/submit
 * Submit a new word decomposition or correction for review.
 */
async function handleSubmit(request: Request, _env: Env): Promise<Response> {
  const body = await request.json<{
    type?: string;
    word?: string;
    data?: Record<string, unknown>;
  }>();

  if (!body.type || !['decomposition', 'correction', 'domain'].includes(body.type)) {
    return errorResponse(
      'Missing or invalid field: type (must be decomposition, correction, or domain)',
      400,
      request,
    );
  }

  // TODO: Validate submission fields based on type
  // TODO: Run submission through Claude Haiku for AI confidence scoring
  // TODO: Insert into D1 (decompositions, corrections, or domain_suggestions table)
  // TODO: Return the created record with status=pending_review

  return jsonResponse(
    {
      status: 'pending_review',
      message: `Submission of type '${body.type}' received. Review pending.`,
      id: null, // Will be D1 autoincrement ID
    },
    201,
    request,
  );
}

/**
 * GET /api/browse
 * Query decompositions with optional filters.
 * Query params: ?domain=legal&status=approved&q=search&limit=50&offset=0
 */
async function handleBrowse(request: Request, _env: Env): Promise<Response> {
  const url = new URL(request.url);
  const domain = url.searchParams.get('domain') || 'all';
  const status = url.searchParams.get('status') || 'approved';
  const query = url.searchParams.get('q') || '';
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '50', 10), 200);
  const offset = parseInt(url.searchParams.get('offset') || '0', 10);

  // TODO: Query D1 decompositions table with filters
  // SELECT * FROM decompositions
  //   WHERE (domain = ? OR ? = 'all')
  //     AND status = ?
  //     AND (word LIKE ? OR true_meaning LIKE ?)
  //   ORDER BY word ASC
  //   LIMIT ? OFFSET ?

  return jsonResponse(
    {
      results: [],
      total: 0,
      filters: { domain, status, query, limit, offset },
    },
    200,
    request,
  );
}

/**
 * GET /api/moderate
 * Moderation queue for pending submissions.
 * Query params: ?type=decomposition&limit=20
 */
async function handleModerate(request: Request, _env: Env): Promise<Response> {
  const url = new URL(request.url);
  const type = url.searchParams.get('type') || 'all';
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '20', 10), 100);

  // TODO: Query D1 for pending_review items across tables
  // TODO: Add authentication/authorization check for moderators

  return jsonResponse(
    {
      queue: [],
      total: 0,
      filters: { type, limit },
    },
    200,
    request,
  );
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const { pathname } = url;
    const method = request.method;

    // CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(request),
      });
    }

    // Rate limit check
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const rateCheck = await checkRateLimit(env.RATE_LIMIT, ip, pathname);
    if (!rateCheck.allowed) {
      return errorResponse('Rate limit exceeded. Please try again later.', 429, request);
    }

    try {
      // Route matching
      if (method === 'POST' && pathname === '/api/ask') {
        return await handleAsk(request, env);
      }
      if (method === 'POST' && pathname === '/api/submit') {
        return await handleSubmit(request, env);
      }
      if (method === 'GET' && pathname === '/api/browse') {
        return await handleBrowse(request, env);
      }
      if (method === 'GET' && pathname === '/api/moderate') {
        return await handleModerate(request, env);
      }

      return errorResponse('Not found', 404, request);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Internal server error';
      console.error('Unhandled error:', message);
      return errorResponse(message, 500, request);
    }
  },
};
