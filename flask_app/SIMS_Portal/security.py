"""
HTTP security headers added to every response.

These are part of a compliance requirement for AmRC hosting on AWS; see
https://learn-sims.org/portal-documentation/adding-and-updating-security-headers/
When adding a new CDN or third-party script, add its origin to the matching
directive below or the browser will block it.
"""

CONTENT_SECURITY_POLICY = '; '.join([
	"default-src 'self'",
	"img-src 'self' data: https://www.google.com https://www.gstatic.com",
	"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://d3js.org https://unpkg.com "
	"https://www.google.com https://www.googletagmanager.com https://cdnjs.cloudflare.com https://ajax.googleapis.com "
	"https://maxcdn.bootstrapcdn.com https://cdn.datatables.net https://www.gstatic.com",
	"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdn.datatables.net "
	"https://maxcdn.bootstrapcdn.com",
	"font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.jsdelivr.net "
	"https://maxcdn.bootstrapcdn.com data:",
	"connect-src 'self' https://www.google-analytics.com https://www.gstatic.com",
	"frame-src 'self' https://www.google.com https://www.gstatic.com https://recaptcha.net",
	"child-src 'self' https://www.google.com https://www.gstatic.com https://recaptcha.net",
	"object-src 'none'",
]) + ';'

SECURITY_HEADERS = {
	'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
	'X-Content-Type-Options': 'nosniff',
	'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
	'X-Frame-Options': 'DENY',
	'Content-Security-Policy': CONTENT_SECURITY_POLICY,
}


def init_security_headers(app):
	@app.after_request
	def add_security_headers(response):
		response.headers.update(SECURITY_HEADERS)
		return response
