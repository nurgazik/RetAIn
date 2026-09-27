import WebKit

/// Reads a page that arrived only as a link (Chrome, other apps' Share buttons): the phone loads
/// it in a hidden web view and runs the Safari page script on it, so both routes share one
/// extractor. No cookies (non-persistent store), so paywalled and logged-in pages come back short.
@MainActor
enum PageFetcher {
    /// The page script's result dict (same keys as Safari's preprocessing results), or nil.
    /// `script` defaults to the bundled RetAInPage.js (tests pass it in: the app bundle lacks it).
    static func fetch(_ url: URL, timeout: Duration = .seconds(10), script: String? = nil) async -> [String: Any]? {
        guard let js = script ?? Bundle.main.url(forResource: "RetAInPage", withExtension: "js")
                .flatMap({ try? String(contentsOf: $0, encoding: .utf8) }) else { return nil }
        let cfg = WKWebViewConfiguration()
        cfg.websiteDataStore = .nonPersistent()
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800), configuration: cfg)
        let nav = LoadWaiter()
        web.navigationDelegate = nav
        web.load(URLRequest(url: url))
        // Many pages never "finish" (trackers, long polls); after the timeout, read what's there.
        guard await nav.wait(timeout: timeout) else { return nil }
        let json = try? await web.evaluateJavaScript(js + """

            ;var out = null; ExtensionPreprocessingJS.run({completionFunction: function (r) { out = r; }});
            JSON.stringify(out)
            """) as? String
        return json.flatMap { try? JSONSerialization.jsonObject(with: Data($0.utf8)) as? [String: Any] }
    }

    /// Resumes once: true when the page finished or the timeout passed, false when the load failed.
    @MainActor private final class LoadWaiter: NSObject, WKNavigationDelegate {
        private var cont: CheckedContinuation<Bool, Never>?
        private var result: Bool?

        func wait(timeout: Duration) async -> Bool {
            if let result { return result }
            return await withCheckedContinuation { c in
                cont = c
                Task { try? await Task.sleep(for: timeout); self.finish(true) }
            }
        }
        private func finish(_ ok: Bool) {
            guard result == nil else { return }
            result = ok
            cont?.resume(returning: ok); cont = nil
        }
        func webView(_ w: WKWebView, didFinish n: WKNavigation!) { finish(true) }
        func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { finish(false) }
        func webView(_ w: WKWebView, didFailProvisionalNavigation n: WKNavigation!, withError e: Error) { finish(false) }
    }
}
