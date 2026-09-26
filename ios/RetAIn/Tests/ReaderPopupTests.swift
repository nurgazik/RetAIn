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
        let body = "<p>Source sentence. <span class=\"note supplement\" data-tier=\"supplement\">"
            + "Robot arms are <mark data-def=\"found everywhere\">ubiquitous</mark> in factories.</span></p>"
        let html = PieceHTML.page(title: "T", label: "Your read", body: body, attrib: "attrib")
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(html, baseURL: nil)
        try await nav.wait()
        _ = try await web.evaluateJavaScript("document.querySelector('.note').click(); true")
        let notePop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(notePop.contains("Added by RetAIn"), notePop)
        _ = try await web.evaluateJavaScript("document.querySelector('mark').click(); true")
        let wordPop = try await web.evaluateJavaScript("document.getElementById('pop').innerText") as? String ?? ""
        XCTAssertTrue(wordPop.contains("found everywhere"), wordPop)
        XCTAssertFalse(wordPop.contains("Added by RetAIn"), wordPop)
    }

    /// D40: rephrased sentences and notes get a margin bar per line (solid vs dotted class);
    /// a substitution gets none; nothing in the text is underlined.
    func testMarginBarsPerTierAndNoUnderline() async throws {
        let body = "<p><span class=\"edited substitute\" data-tier=\"substitute\" data-orig=\"A.\">They <mark data-def=\"x\">bolster</mark> it.</span></p>"
            + "<p><span class=\"edited rephrase\" data-tier=\"rephrase\" data-orig=\"B.\">" + String(repeating: "A long rephrased sentence keeps going. ", count: 6) + "</span>"
            + " <span class=\"note supplement\" data-tier=\"supplement\">A note with a <mark data-def=\"y\">word</mark>.</span></p>"
        let html = PieceHTML.page(title: "T", label: "Your read", body: body, attrib: "attrib")
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(html, baseURL: nil)
        try await nav.wait()
        let rephraseBars = try await web.evaluateJavaScript("document.querySelectorAll('.bar-rephrase').length") as? Int ?? 0
        let noteBars = try await web.evaluateJavaScript("document.querySelectorAll('.bar-note').length") as? Int ?? 0
        let subTop = try await web.evaluateJavaScript("document.querySelector('.substitute').getBoundingClientRect().top") as? Double ?? 0
        let barTops = try await web.evaluateJavaScript("Array.from(document.querySelectorAll('.bar')).map(b => parseFloat(b.style.top))") as? [Double] ?? []
        let underline = try await web.evaluateJavaScript("getComputedStyle(document.querySelector('.rephrase')).textDecorationLine") as? String ?? ""
        XCTAssertGreaterThanOrEqual(rephraseBars, 3, "a multi-line rephrase gets a bar per line")
        XCTAssertGreaterThanOrEqual(noteBars, 1)
        XCTAssertFalse(barTops.contains { abs($0 - subTop) < 12 }, "no bar beside the substitution")
        XCTAssertEqual(underline, "none")
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
