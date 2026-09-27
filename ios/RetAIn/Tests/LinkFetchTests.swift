import XCTest
@testable import RetAIn

/// A share that arrives as a link only (Chrome, most apps' Share buttons): the extension reads
/// the page on the phone with the Safari page script.
@MainActor
final class LinkFetchTests: XCTestCase {
    private func linkOnly(_ url: String = "https://www.cbc.ca/news/politics/x") -> ExtensionInput {
        var r = ExtensionInput(source: "share-ext"); r.url = url; r.typeLog = ["public.url"]; return r
    }
    private static let article = Array(repeating: "Archivists report a sharp increase in requests for records.", count: 6).joined(separator: " ")

    func testLinkOnlyFetchesThePage() async {
        var r = linkOnly()
        await r.readLink { _ in ["text": Self.article, "title": "Archives swamped", "extractor": "readability",
                                 "byline": "Elizabeth Thompson", "selection": ""] }
        XCTAssertEqual(r.effectiveText, Self.article)
        XCTAssertEqual(r.extractor, "fetched-readability")
        XCTAssertEqual(r.linkFetch, "ok")
        XCTAssertEqual(r.title, "Archives swamped")
        XCTAssertEqual(r.sourceFields["byline"], "Elizabeth Thompson")
        XCTAssertEqual(r.url, "https://www.cbc.ca/news/politics/x")   // the shared link, not the page's
    }

    func testFailedLoadExplainsItself() async {
        var r = linkOnly()
        await r.readLink { _ in nil }
        XCTAssertNil(r.effectiveText)
        XCTAssertEqual(r.linkFetch, "failed")
        XCTAssertEqual(r.unusableReason.title, "Couldn't read this page")
    }

    func testPaywallStubIsShort() async {
        var r = linkOnly()
        await r.readLink { _ in ["text": "Subscribe to keep reading.", "extractor": "innerText"] }
        XCTAssertEqual(r.linkFetch, "short")
        XCTAssertEqual(r.unusableReason.title, "Couldn't read this page")
    }

    func testNoFetchWhenTextArrivedOrNotWeb() async {
        var called = false
        var withText = linkOnly(); withText.text = Self.article
        await withText.readLink { _ in called = true; return nil }
        var word = linkOnly(); word.text = "bolster"
        await word.readLink { _ in called = true; return nil }
        var mail = linkOnly("mailto:a@b.c")
        await mail.readLink { _ in called = true; return nil }
        XCTAssertFalse(called)
        XCTAssertNil(withText.linkFetch)
    }

    /// Real sites over the network; opt-in (RETAIN_NET_PROBE=1) since it depends on them.
    func testFetcherOnLiveArticles() async throws {
        guard ProcessInfo.processInfo.environment["RETAIN_NET_PROBE"] == "1" else { throw XCTSkip("RETAIN_NET_PROBE not set") }
        let js = try String(contentsOf: URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("../ActionExt/RetAInPage.js").standardized, encoding: .utf8)
        for s in ["https://www.bbc.com/news/articles/c0l0k4389g2o", "https://en.wikipedia.org/wiki/Readability",
                  "https://techcrunch.com/"] {
            let t0 = Date()
            let res = await PageFetcher.fetch(URL(string: s)!, script: js)
            let words = (res?["text"] as? String ?? "").split(whereSeparator: { $0.isWhitespace }).count
            print("PROBE \(s) extractor=\(res?["extractor"] as? String ?? "nil") words=\(words) secs=\(Int(Date().timeIntervalSince(t0)))")
        }
    }

    /// The real fetcher: hidden web view, page script, no network (a data: URL).
    func testFetcherRunsPageScript() async throws {
        let src = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("../ActionExt/RetAInPage.js").standardized
        let js = try String(contentsOf: src, encoding: .utf8)
        let url = URL(string: "data:text/html;base64," + Data(PageScriptTests.page.utf8).base64EncodedString())!
        let res = await PageFetcher.fetch(url, script: js)
        let text = res?["text"] as? String ?? ""
        XCTAssertEqual(res?["extractor"] as? String, "readability")
        XCTAssertTrue(text.contains("Lafayette, Louisiana"), text)
        XCTAssertFalse(text.contains("Social Sharing"), text)
    }
}
