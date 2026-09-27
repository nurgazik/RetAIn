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

    // MARK: Facebook

    /// A public page's post as Facebook serves it logged out (2026-09-27), trimmed: the post's
    /// text cut at "... See more", a separate See more button, and the page's other posts.
    private static let fbPost = """
        <html><head><title>Short Stories - After my affair came to light… | Facebook</title>
        <meta property="og:title" content="Short Stories">
        <meta property="og:description" content="After my affair came to light, my husband never touched me again. For 18 years...">
        </head><body>
        <div data-successful-render-id="122141952087346577">
          <div role="button" aria-expanded="false" id="toggle"><div dir="auto" id="post">After my affair came to light, my husband never touched me again. For 18 years...</div></div>
          <div role="button" id="more"><span>... See more</span></div>
          <div dir="auto">PART 2: a long comment by the page that must not be read, \(article)</div>
          <div dir="auto">Another post by the page… <div role="button" id="other"><span>... See more</span></div></div>
        </div>
        <script>
        document.getElementById('other').addEventListener('click', function () { document.getElementById('post').innerText = 'WRONG BUTTON'; });
        document.getElementById('toggle').addEventListener('click', function () {
          setTimeout(function () {
            document.getElementById('post').innerText = 'After my affair came to light, my husband never touched me again. For 18 years, we lived under the same roof like strangers. \(article) Her expression changed...';
          }, 300);
        });
        </script></body></html>
        """
    private func facebook(_ url: String, html: String) async throws -> ReaderResult {
        let loaded = await PageLoader.open(html: html, baseURL: URL(string: url)!, until: FacebookReader.ready, timeout: .seconds(2))
        return await FacebookReader().extract(from: try XCTUnwrap(loaded))
    }

    func testFacebookPublicPostExpandsSeeMore() async throws {
        guard case .text(let r) = try await facebook("https://www.facebook.com/story.php?story_fbid=122141952087346577&id=61590397333180",
                                                     html: Self.fbPost) else { return XCTFail() }
        XCTAssertEqual(r.extractor, "facebook-post")
        XCTAssertTrue(r.text.hasPrefix("After my affair came to light"), r.text)
        XCTAssertTrue(r.text.hasSuffix("Her expression changed..."), r.text)      // the page's own cliffhanger stays
        XCTAssertFalse(r.text.contains("PART 2"))
        XCTAssertEqual(r.sourceFields, ["byline": "Short Stories", "site_name": "Facebook"])
    }

    func testFacebookPrivateGroupIsNamed() async throws {
        let html = """
            <html><head><meta property="og:title" content="Built with Science Private Community | Facebook">
            <meta property="og:description" content="Welcome to the Built With Science Private Community!"></head>
            <body><div dir="auto">Welcome to the Built With Science Private Community! This community is for members only.</div>
            Private group · 70.2K members. Log in to see posts and join the conversation.</body></html>
            """
        guard case .unusable(let title, let detail) = try await facebook("https://www.facebook.com/groups/2282990221717294/", html: html)
        else { return XCTFail() }
        XCTAssertEqual(title, "This post is in a private group")
        XCTAssertTrue(detail.contains("“Built with Science Private Community”"), detail)
    }

    func testFacebookLoginWall() async throws {
        let html = """
            <html><head><meta property="og:title" content="Log into Facebook | Facebook"></head>
            <body>Mobile number or email Password Log in</body></html>
            """
        guard case .unusable(let title, _) = try await facebook("https://m.facebook.com/login/?next=https%3A%2F%2Fwww.facebook.com%2Fshare%2Fp%2Fx", html: html)
        else { return XCTFail() }
        XCTAssertEqual(title, "Facebook wants a login for this post")
    }

    /// Facebook's share sheet sends the link as plain text; it must still reach the link readers.
    func testLinkSharedAsTextIsALink() {
        var i = input(text: " https://www.facebook.com/share/1DZxoEEMzn/?mibextid=wwXIfr\n")
        i.promoteLinkText()
        XCTAssertEqual(i.url, "https://www.facebook.com/share/1DZxoEEMzn/?mibextid=wwXIfr")
        XCTAssertNil(i.text)
        XCTAssertEqual(claimant(i), "facebook")
        var words = input(text: "see https://example.com for more")
        words.promoteLinkText()
        XCTAssertNil(words.url)
    }

    /// Real sites over the network; opt-in (RETAIN_NET_PROBE=1) since it depends on them.
    func testLiveLinks() async throws {
        guard ProcessInfo.processInfo.environment["RETAIN_NET_PROBE"] == "1" else { throw XCTSkip("RETAIN_NET_PROBE not set") }
        let web = WebPageReader(script: Self.pageScript)
        let router = ShareRouter(readers: [RedditReader(), FacebookReader(), web])
        for s in ["https://www.reddit.com/r/ClaudeAI/s/nlvL3JzYxD", "https://www.reddit.com/r/economy/s/RP0roaa0QK",
                  "https://en.wikipedia.org/wiki/Readability", "https://www.facebook.com/share/1DZxoEEMzn/?mibextid=wwXIfr",
                  "https://www.facebook.com/share/p/189EK24aX6/?mibextid=wwXIfr", "https://www.facebook.com/share/p/189qwrP5XX/?mibextid=wwXIfr"] {
            let t0 = Date()
            let out: String
            switch await router.route(input(url: s)) {
            case .read(let r, let reader): out = "\(reader) \(r.extractor) words=\(Words.count(r.text)) title=\(r.title ?? "") fields=\(r.sourceFields) url=\(r.url ?? "") head=\(r.text.prefix(80))"
            case .unusable(let t, let d, let reader): out = "\(reader) UNUSABLE \(t) — \(d)"
            case .capture: out = "capture"
            }
            print(String(format: "PROBE %.1fs ", Date().timeIntervalSince(t0)) + s + " → " + out)
        }
    }
}
