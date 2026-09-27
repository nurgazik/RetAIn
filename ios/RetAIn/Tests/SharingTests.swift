import XCTest
@testable import RetAIn

/// The share router and its readers (Shared/Sharing/): which reader claims a share, and what
/// each reads from its source's saved page.
@MainActor
final class SharingTests: XCTestCase {
    private static let article = Array(repeating: "Archivists report a sharp increase in requests for records.", count: 6).joined(separator: " ")
    private static let pageScript: String = {
        let src = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("../ActionExt/RetAInPage.js").standardized
        return (try? String(contentsOf: src, encoding: .utf8)) ?? ""
    }()
    private func input(text: String? = nil, url: String? = nil, page: [String: Any]? = nil) -> ShareInput {
        ShareInput(text: text, url: url, pageScript: page)
    }
    private func claimant(_ i: ShareInput) -> String? { ShareRouter().readers.first { $0.claims(i) }?.name }

    // MARK: routing

    func testRouterOrder() {
        let page: [String: Any] = ["text": Self.article, "selection": Self.article]
        XCTAssertEqual(claimant(input(url: "https://cbc.ca/x", page: page)), "selection")
        XCTAssertEqual(claimant(input(url: "https://cbc.ca/x", page: ["text": Self.article, "selection": "one two"])), "safari-page")
        XCTAssertEqual(claimant(input(text: Self.article, url: "https://www.reddit.com/r/a/comments/b/c/")), "plain-text")
        XCTAssertEqual(claimant(input(url: "https://www.reddit.com/r/ClaudeAI/s/nlvL3JzYxD")), "reddit")
        XCTAssertEqual(claimant(input(url: "https://old.reddit.com/r/a/comments/b/c/")), "reddit")
        XCTAssertEqual(claimant(input(url: "https://en.wikipedia.org/wiki/Readability")), "web-page")
        XCTAssertEqual(claimant(input(text: "short title", url: "https://notreddit.com/x")), "web-page")
        XCTAssertNil(claimant(input(url: "mailto:a@b.c")))
    }

    func testWordIsCaptureAndNothingExplainsItself() async {
        guard case .capture("bolster") = await ShareRouter().route(input(text: "Bolster.")) else { return XCTFail("capture") }
        guard case .unusable("A little more, please", _, "none") = await ShareRouter().route(input(text: "just five words right here")) else { return XCTFail("short") }
        guard case .unusable("Nothing to read here", _, "none") = await ShareRouter().route(input()) else { return XCTFail("empty") }
    }

    func testSafariPageKeepsHeaderFields() async {
        let page: [String: Any] = ["text": Self.article, "title": "Archives swamped", "extractor": "readability",
                                   "byline": "Elizabeth Thompson", "siteName": "CBC", "dek": ""]
        guard case .read(let r, "safari-page") = await ShareRouter().route(input(url: "https://cbc.ca/x", page: page)) else { return XCTFail() }
        XCTAssertEqual(r.title, "Archives swamped")
        XCTAssertEqual(r.sourceFields, ["byline": "Elizabeth Thompson", "site_name": "CBC"])
        XCTAssertEqual(r.extractor, "readability")
    }

    // MARK: page loading

    /// A script check page first, the real page 0.6 s later: the loader waits for the reader's
    /// ready test, not the first load.
    func testLoaderWaitsPastCheckPage() async {
        let html = """
            <html><body><p>Please wait</p><script>
            setTimeout(function () { document.body.innerHTML = '<shreddit-post post-title="T"></shreddit-post>'; }, 600);
            </script></body></html>
            """
        let page = await PageLoader.open(html: html, baseURL: URL(string: "https://www.reddit.com/r/a/comments/b/c/")!,
                                         until: "!!document.querySelector('shreddit-post')", timeout: .seconds(5))
        let found = await page?.evaluate("!!document.querySelector('shreddit-post')") as? Bool
        XCTAssertEqual(found, true)
    }

    func testWebPageReaderRunsPageScript() async throws {
        let loaded = await PageLoader.open(html: PageScriptTests.page, baseURL: URL(string: "https://www.cbc.ca/news/politics/x")!,
                                           until: WebPageReader.ready, timeout: .seconds(2))
        let page = try XCTUnwrap(loaded)
        guard case .text(let r) = await WebPageReader(script: Self.pageScript).extract(from: page, url: "https://www.cbc.ca/news/politics/x") else { return XCTFail() }
        XCTAssertEqual(r.extractor, "web-readability")
        XCTAssertTrue(r.text.contains("Lafayette, Louisiana"), r.text)
        XCTAssertFalse(r.text.contains("Social Sharing"), r.text)
    }

    // MARK: Reddit

    /// Reddit's thread markup as of 2026-09-27 (shreddit web components), trimmed.
    private static let thread = """
        <html><head><title>Does anybody else… : r/economy</title></head><body>
        <shreddit-post post-title="Does anybody else have trouble believing rich people don't buy expensive cars?" author="op_user">
          <div slot="text-body"><p>\(article)</p></div>
        </shreddit-post>
        <shreddit-comment thingid="t1_aaa111" author="first_commenter" depth="0">
          <div slot="comment"><p>A different comment that should not be read when the link names another one, \(article)</p></div>
        </shreddit-comment>
        <shreddit-comment thingid="t1_pcdmy8z" author="Canuck-In-TO" depth="0">
          <div slot="comment"><p>I know a number of very wealthy people.</p><p>\(article)</p></div>
        </shreddit-comment>
        </body></html>
        """
    private func reddit(_ path: String, html: String = thread) async throws -> ReaderResult {
        let loaded = await PageLoader.open(html: html, baseURL: URL(string: "https://www.reddit.com" + path)!,
                                           until: "(\(RedditReader.pageJS)).ready", timeout: .seconds(3))
        let page = try XCTUnwrap(loaded)
        return await RedditReader().extract(from: page)
    }

    func testRedditPostLinkReadsThePost() async throws {
        guard case .text(let r) = try await reddit("/r/economy/comments/1wrlyju/does_anybody_else/?share_id=x") else { return XCTFail() }
        XCTAssertEqual(r.extractor, "reddit-post")
        XCTAssertEqual(r.text, Self.article)
        XCTAssertEqual(r.title, "Does anybody else have trouble believing rich people don't buy expensive cars?")
        XCTAssertEqual(r.sourceFields, ["byline": "u/op_user", "site_name": "r/economy"])
        XCTAssertEqual(r.url, "https://www.reddit.com/r/economy/comments/1wrlyju/does_anybody_else/")  // tracking dropped
    }

    func testRedditCommentLinkReadsThatComment() async throws {
        guard case .text(let r) = try await reddit("/r/economy/comments/1wrlyju/comment/pcdmy8z/") else { return XCTFail() }
        XCTAssertEqual(r.extractor, "reddit-comment")
        XCTAssertTrue(r.text.hasPrefix("I know a number of very wealthy people."), r.text)
        XCTAssertFalse(r.text.contains("A different comment"))
        XCTAssertEqual(r.sourceFields["byline"], "u/Canuck-In-TO")
        // the older permalink shape names the comment too
        guard case .text(let old) = try await reddit("/r/economy/comments/1wrlyju/does_anybody_else/pcdmy8z/") else { return XCTFail() }
        XCTAssertEqual(old.extractor, "reddit-comment")
    }

    func testShortRedditPostPointsToComments() async throws {
        let html = Self.thread.replacingOccurrences(of: "<div slot=\"text-body\"><p>\(Self.article)</p></div>",
                                                    with: "<div slot=\"text-body\"><p>What do you think?</p></div>")
        guard case .unusable(let title, let detail) = try await reddit("/r/economy/comments/1wrlyju/x/", html: html) else { return XCTFail() }
        XCTAssertEqual(title, "A short post")
        XCTAssertTrue(detail.contains("share that comment"), detail)
    }

    /// Real sites over the network; opt-in (RETAIN_NET_PROBE=1) since it depends on them.
    func testLiveLinks() async throws {
        guard ProcessInfo.processInfo.environment["RETAIN_NET_PROBE"] == "1" else { throw XCTSkip("RETAIN_NET_PROBE not set") }
        let web = WebPageReader(script: Self.pageScript)
        let router = ShareRouter(readers: [RedditReader(), web])
        for s in ["https://www.reddit.com/r/ClaudeAI/s/nlvL3JzYxD", "https://www.reddit.com/r/economy/s/RP0roaa0QK",
                  "https://en.wikipedia.org/wiki/Readability"] {
            let t0 = Date()
            let out: String
            switch await router.route(input(url: s)) {
            case .read(let r, let reader): out = "\(reader) \(r.extractor) words=\(Words.count(r.text)) title=\(r.title ?? "") fields=\(r.sourceFields) url=\(r.url ?? "") head=\(r.text.prefix(80))"
            case .unusable(let t, _, let reader): out = "\(reader) UNUSABLE \(t)"
            case .capture: out = "capture"
            }
            print(String(format: "PROBE %.1fs ", Date().timeIntervalSince(t0)) + s + " → " + out)
        }
    }
}
