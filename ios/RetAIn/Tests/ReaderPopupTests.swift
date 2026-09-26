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

    /// D40: tapping the sentence reveals the original; tapping the word inside it still
    /// shows the definition, not the original.
    func testSentenceTapRevealsOriginalWordTapShowsMeaning() async throws {
        let body = "<p><span class=\"edited rephrase\" data-tier=\"rephrase\" data-orig=\"They &quot;confirm&quot; it.\">"
            + "They <mark data-def=\"to support\">bolster</mark> it.</span> Rest.</p>"
        let html = PieceHTML.page(title: "T", label: "Your read", body: body, attrib: "attrib")
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(html, baseURL: nil)
        try await nav.wait()
        _ = try await web.evaluateJavaScript("document.querySelector('.edited').click(); true")
        let sentencePop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(sentencePop.contains("Sentence rephrased"), sentencePop)
        XCTAssertTrue(sentencePop.contains("They \"confirm\" it."), sentencePop)
        _ = try await web.evaluateJavaScript("document.querySelector('mark').click(); true")
        let wordPop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(wordPop.contains("to support"), wordPop)
        XCTAssertFalse(wordPop.contains("original"), wordPop)
    }

    /// D40: tapping a note says it was added by RetAIn; tapping its word shows the meaning.
    func testNoteTapExplainsOriginWordTapShowsMeaning() async throws {
        let body = "<p>Source paragraph.</p><aside class=\"supplement\" data-tier=\"supplement\">"
            + "Robot arms are <mark data-def=\"found everywhere\">ubiquitous</mark> in factories.</aside>"
        let html = PieceHTML.page(title: "T", label: "Your read", body: body, attrib: "attrib")
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(html, baseURL: nil)
        try await nav.wait()
        _ = try await web.evaluateJavaScript("document.querySelector('aside').click(); true")
        let notePop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(notePop.contains("Added by RetAIn"), notePop)
        _ = try await web.evaluateJavaScript("document.querySelector('mark').click(); true")
        let wordPop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(wordPop.contains("found everywhere"), wordPop)
        XCTAssertFalse(wordPop.contains("Added by RetAIn"), wordPop)
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
