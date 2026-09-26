import WebKit
import XCTest

/// Runs the Safari extension's page script (Readability + RetAInPage) against a news-style
/// page full of clutter, the way Safari does before the sheet opens.
@MainActor
final class PageScriptTests: XCTestCase {
    static let page = """
    <html><head><title>Archives swamped | CBC News</title></head><body>
    <nav><a href="/">Home</a> <a href="/politics">Politics</a></nav>
    <div class="social-share share-bar">Social Sharing X Reddit LinkedIn Show More</div>
    <main><article>
      <h1>Change in Canada's citizenship law hitting U.S. archives</h1>
      <div class="byline">Elizabeth Thompson · CBC News</div>
      <div class="audio-player">Listen to this article Estimated 7 minutes</div>
      <p>Sitting in their archive in Lafayette, Louisiana, Barbara Dejean and Stephanie Simon first heard about a change in Canada's citizenship rules in December, when they read an online news story. Then the calls started coming in.</p>
      <p>Calls from Americans who wanted to document their Canadian ancestry, sometimes going back several generations, arrived by the dozen every week, and the small team soon had a backlog that stretched for months.</p>
      <p>Archivists in several other states report the same pattern: a sharp increase in requests for records, longer processing times, and staff pulled away from their usual work to answer genealogical questions.</p>
      <p>The law extends citizenship to people who can show they have a Canadian ancestor, which has turned church registers, census rolls and old immigration papers into documents of real consequence.</p>
    </article></main>
    <footer>Copyright CBC · Terms of use · Privacy</footer>
    </body></html>
    """

    func testReadabilityDropsClutterAndKeepsParagraphs() async throws {
        let src = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("../ActionExt/RetAInPage.js").standardized
        let js = try String(contentsOf: src, encoding: .utf8)
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = ReaderPopupTests.NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(Self.page, baseURL: URL(string: "https://www.cbc.ca/news/politics/x"))
        try await nav.wait()
        _ = try await web.evaluateJavaScript(js + "\n;true")
        let json = try await web.evaluateJavaScript("""
            var out = null; ExtensionPreprocessingJS.run({completionFunction: function (r) { out = r; }});
            JSON.stringify(out)
            """) as? String ?? "{}"
        let r = try JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: String] ?? [:]
        let text = r["text"] ?? ""
        XCTAssertEqual(r["extractor"], "readability", json)
        XCTAssertTrue(text.contains("Sitting in their archive"), text)
        XCTAssertFalse(text.contains("Social Sharing"), text)
        XCTAssertFalse(text.contains("Copyright CBC"), text)
        XCTAssertFalse(text.contains("Listen to this article"), text)
        XCTAssertEqual(r["title"], "Change in Canada's citizenship law hitting U.S. archives", json)
        XCTAssertEqual(r["byline"], "Elizabeth Thompson · CBC News", json)
        XCTAssertEqual(text.components(separatedBy: "\n\n").count, 4, json)
    }
}
