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

    /// Runs the page script on `page` the way Safari does; returns its result and the raw JSON.
    private func extract(_ page: String) async throws -> ([String: String], String) {
        let src = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .appendingPathComponent("../ActionExt/RetAInPage.js").standardized
        let js = try String(contentsOf: src, encoding: .utf8)
        let web = WKWebView(frame: CGRect(x: 0, y: 0, width: 390, height: 800))
        let nav = ReaderPopupTests.NavSink()
        web.navigationDelegate = nav
        web.loadHTMLString(page, baseURL: URL(string: "https://www.cbc.ca/news/politics/x"))
        try await nav.wait()
        _ = try await web.evaluateJavaScript(js + "\n;true")
        let json = try await web.evaluateJavaScript("""
            var out = null; ExtensionPreprocessingJS.run({completionFunction: function (r) { out = r; }});
            JSON.stringify(out)
            """) as? String ?? "{}"
        return ((try JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: String]) ?? [:], json)
    }

    func testReadabilityDropsClutterAndKeepsParagraphs() async throws {
        let (r, json) = try await extract(Self.page)
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

    /// CBC's real header region (p_0344f5cd95bd43ba, fetched 2026-09-27; scripts, images and
    /// svgs stripped except the JSON-LD fields Readability reads; CBC's own wrapper divs kept, since Readability's choice of
    /// container depends on them): section label, summary, sub-headline, byline + dateline and a collapsed
    /// AI-audio note, all of which used to land in the body as prose. The <style> rule stands
    /// in for CBC's stylesheet, which hides the collapsed note. (CBC's stylesheet also hides the
    /// summary at every width; here it is visible, as on sites that show theirs, to test the dek.)
    static let cbcHeader = """
    <html><head><title>Canadian citizen detained at U.S. border crossing, questioned for hours about voting | CBC News</title>
    <meta name="description" content="Paige Adamson was on her way home from a birthday dinner in Tsawwassen, B.C., on Sept. 15 when she was stopped at the Point Roberts border crossing and questioned about voting for hours. Lawyers are raising concerns around vulnerabilities Canadians face while living in the U.S., especially over being registered to vote.">
    <script type="application/ld+json">{"@context":"https://schema.org","@type":"ReportageNewsArticle","headline":"Canadian citizen detained at U.S. border crossing, questioned for hours about voting","datePublished":"2026-09-26T12:00:00.000Z","publisher":{"@type":"NewsMediaOrganization","name":"CBC"},"author":[{"@type":"Person","name":"Arden McLeod"}]}</script>
    <style>.toggletipInfoText-Us8br[data-status="false"] { display: none; }</style></head><body class="feed"><div id="app">
    <main class="feed-content content" id="content"><div class="detail detailBody pageComponent">
    <div class="detailBodyContainer withSidebar"><div class="withFlex"><div class="detailMainCol sclt-storycontent" id="detailContent">
    <span class="detail-link-label sclt-storySectionLink"><a class="" href="/news/canada/british-columbia"><span>British Columbia</span></a></span><h1 class="detailHeadline" lang="en">Canadian citizen detained at U.S. border crossing, questioned for hours about voting</h1><div class="detailSummary">Paige Adamson was on her way home from a birthday dinner in Tsawwassen, B.C., on Sept. 15 when she was stopped at the Point Roberts border crossing and questioned about voting for hours. Lawyers are raising concerns around vulnerabilities Canadians face while living in the U.S., especially over being registered to vote.</div><h2 class="deck" lang="en">&#x27;Tip of the iceberg&#x27;: One lawyer warns more Canadians could be detained over illegal voting concerns</h2><div class="byline"><figure class="imageMedia-IspZw imageMedia author-image full"><div class="placeholder-cWBmZ placeholder"></div></figure><div class="bylineDetails"><span class="authorText"><a class="" href="/author/arden-mcleod-9.14506">Arden McLeod</a></span> <span class="bullet"> · </span>CBC News <span class="bullet"> · </span><time class="timeStamp" dateTime="2026-09-26T12:00:00.000Z">Posted: Sep 26, 2026 8:00 AM EDT | Last Updated: September 26</time></div></div><div><div class="textToSpeech-p16Ki"><div class="ttsPlayPauseWrapper-M3HPC"><button type="button" class="ttsPlayPauseButton-b4Yle" aria-label="Play audio"></button></div><div class="ttsIcon-cIBsl"></div><div><div class="ttsText-ImVhZ">Listen to this article</div><div class="ttsStatusMessage-XsLQw">Estimated 5 minutes</div></div><div class="toggletip-tKLKF ttsToggleTip-DSCNQ"><button type="button" class="toggletipInfoButton-yoX4E" aria-label="More information" aria-controls=":R89qn5:" aria-describedby=":R89qn5:" aria-expanded="false"></button><div id=":R89qn5:" class="toggletipInfoText-Us8br" data-status="false">The audio version of this article is generated by AI-based technology. Mispronunciations can occur. We are working with our partners to continually review and improve the results.</div></div></div><figure class="imageMedia-IspZw imageMedia leadmedia-story full"><div class="placeholder-cWBmZ placeholder"><picture><source media="(max-width: 480px)"/></picture></div><figcaption class="image-caption">Paige Adamson says she was detained until nearly 3 a.m. PT and was &#x27;basically treated like a criminal&#x27; when she attempted to cross the Canada-U.S. border at the Point Roberts border crossing on Sept. 15. (Ben Nelms/CBC)</figcaption></figure><div class="engagement-widgets"><div class="share"><h2 class="a11y">Social Sharing</h2><div class="viafoura"></div></div></div><div class="story"><p>Paige Adamson was on her way home from a birthday dinner in Tsawwassen, B.C., on Sept. 15 when she was stopped at the Point Roberts border crossing.</p><p>It was a regular stop that Adamson — a Canadian citizen who has lived in Point Roberts, Wash., as a U.S. permanent resident for 14 years — had grown used to.</p><p>But this time, they had a new question for her.</p><p>&quot;The very first thing she asked was, &#x27;Have you ever voted in a federal U.S. election?&#x27;&quot; said Adamson.</p><p>Adamson, 61, said she told the border agent she had never voted in a federal election.</p></div>
    </div></div></div></div></main></div></body></html>
    """

    func testPageMetadataGoesToFieldsNotBody() async throws {
        let (r, json) = try await extract(Self.cbcHeader)
        let text = r["text"] ?? ""
        XCTAssertTrue(text.hasPrefix("Paige Adamson was on her way home from a birthday dinner in Tsawwassen, B.C., on Sept. 15 when she was stopped at the Point Roberts border crossing.\n\n"), json)
        XCTAssertFalse(text.contains("Posted:"), json)
        XCTAssertFalse(text.contains("audio version"), json)
        XCTAssertFalse(text.contains("Tip of the iceberg"), json)
        XCTAssertFalse(text.contains("British Columbia\n"), json)
        XCTAssertEqual(r["dek"], "Paige Adamson was on her way home from a birthday dinner in Tsawwassen, B.C., on Sept. 15 when she was stopped at the Point Roberts border crossing and questioned about voting for hours. Lawyers are raising concerns around vulnerabilities Canadians face while living in the U.S., especially over being registered to vote.\n\n'Tip of the iceberg': One lawyer warns more Canadians could be detained over illegal voting concerns", json)
        XCTAssertEqual(r["publishedTime"], "2026-09-26T12:00:00.000Z", json)
        XCTAssertEqual(r["byline"], "Arden McLeod", json)
        XCTAssertEqual(r["siteName"], "CBC", json)
        XCTAssertEqual(r["title"], "Canadian citizen detained at U.S. border crossing, questioned for hours about voting", json)
    }

    /// Some sites' description is just the lede; with no sub-headline or dateline around it,
    /// it is body text and must stay there.
    func testDescriptionThatIsTheLedeStaysInBody() async throws {
        let lede = "Sitting in their archive in Lafayette, Louisiana, Barbara Dejean and Stephanie Simon first heard about a change in Canada's citizenship rules in December, when they read an online news story. Then the calls started coming in."
        let page = Self.page.replacingOccurrences(of: "<head>", with: "<head><meta name=\"description\" content=\"\(lede)\">")
            .replacingOccurrences(of: "<div class=\"audio-player\">Listen to this article Estimated 7 minutes</div>", with: "")  // lede comes first
        let (r, json) = try await extract(page)
        XCTAssertTrue((r["text"] ?? "").hasPrefix("Sitting in their archive"), json)
        XCTAssertEqual(r["dek"], "", json)
    }
}
