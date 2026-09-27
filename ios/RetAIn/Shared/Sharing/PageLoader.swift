import WebKit

/// A page loaded on the phone in a hidden web view, for readers that only got a link.
/// No cookies (non-persistent store), so paywalled and logged-in pages come back short.
///
/// "Finished loading" isn't "ready": some sites (Reddit) first serve a script check that then
/// redirects to the real page. So the loader polls the reader's own `ready` test (a JavaScript
/// expression) until it holds or the timeout passes, then hands the page over either way.
@MainActor
final class PageLoader: NSObject, WKNavigationDelegate {
    private let web: WKWebView
    private var failed = false

    private override init() {
        let cfg = WKWebViewConfiguration()
        cfg.websiteDataStore = .nonPersistent()
        web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800), configuration: cfg)
        super.init()
        web.navigationDelegate = self
    }

    /// The loaded page, or nil when it didn't load at all.
    static func open(_ url: URL, until ready: String, timeout: Duration = .seconds(10)) async -> PageLoader? {
        let page = PageLoader()
        page.web.load(URLRequest(url: url))
        return await page.settle(until: ready, timeout: timeout)
    }
    /// Tests: a saved page, as if it had loaded from `baseURL`.
    static func open(html: String, baseURL: URL, until ready: String, timeout: Duration = .seconds(10)) async -> PageLoader? {
        let page = PageLoader()
        page.web.loadHTMLString(html, baseURL: baseURL)
        return await page.settle(until: ready, timeout: timeout)
    }

    func evaluate(_ js: String) async -> Any? { try? await web.evaluateJavaScript(js) }
    var currentURL: URL? { web.url }

    /// Polls `ready` (a JavaScript expression): true once it holds, false on timeout or a failed load.
    /// Also for a second step after interacting with the page (e.g. waiting for "See more" to expand).
    func wait(until ready: String, timeout: Duration) async -> Bool {
        let clock = ContinuousClock(), end = clock.now + timeout
        while clock.now < end && !failed {
            if await evaluate("!!(\(ready))") as? Bool == true { return true }
            try? await Task.sleep(for: .milliseconds(250))
        }
        return false
    }
    /// After the first load: the page whether or not it got ready (readers judge what's there), nil if it failed.
    private func settle(until ready: String, timeout: Duration) async -> PageLoader? {
        _ = await wait(until: ready, timeout: timeout)
        return failed ? nil : self
    }

    // A redirect cancels the navigation before it (NSURLErrorCancelled): that isn't a failure.
    private func fail(_ e: Error) { if (e as NSError).code != NSURLErrorCancelled { failed = true } }
    func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { fail(e) }
    func webView(_ w: WKWebView, didFailProvisionalNavigation n: WKNavigation!, withError e: Error) { fail(e) }
}
