import WebKit
import XCTest
@testable import RetAIn

/// Loads the reader page into an offscreen WKWebView and drives the popup with JavaScript:
/// a mark click must show the definition and "Seen N times", and the "Got it" button must
/// post the retain message.
@MainActor
final class ReaderPopupTests: XCTestCase {
    func testPopupShowsStatsAndPostsRetain() async throws {
        let html = PieceHTML.page(title: "T", label: "Your read",
                                  body: "<p>We <mark data-def=\"to support\">bolster</mark> it.</p>",
                                  attrib: "attrib", stats: ["bolster": [7, 2]])
        let cfg = WKWebViewConfiguration()
        let sink = Sink()
        cfg.userContentController.add(sink, name: "tap")
        cfg.userContentController.add(sink, name: "retain")
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800), configuration: cfg)
        let nav = NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(html, baseURL: nil)
        try await nav.wait()
        _ = try await web.evaluateJavaScript("document.querySelector('mark').click(); true")
        let popText = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(popText.contains("bolster"), popText)
        XCTAssertTrue(popText.contains("to support"), popText)
        XCTAssertTrue(popText.contains("Seen 3 times"), popText)
        XCTAssertTrue(popText.contains("Got it"), popText)
        _ = try await web.evaluateJavaScript("document.querySelector('#pop button').click(); true")
        try await Task.sleep(nanoseconds: 300_000_000)
        XCTAssertEqual(sink.messages["tap"], "bolster")
        XCTAssertEqual(sink.messages["retain"], "bolster")
    }

    final class Sink: NSObject, WKScriptMessageHandler {
        var messages: [String: String] = [:]
        func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
            messages[m.name] = m.body as? String
        }
    }
    final class NavSink: NSObject, WKNavigationDelegate {
        private var cont: CheckedContinuation<Void, Error>?
        func wait() async throws { try await withCheckedThrowingContinuation { self.cont = $0 } }
        func webView(_ w: WKWebView, didFinish n: WKNavigation!) { cont?.resume(); cont = nil }
        func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { cont?.resume(throwing: e); cont = nil }
    }
}
