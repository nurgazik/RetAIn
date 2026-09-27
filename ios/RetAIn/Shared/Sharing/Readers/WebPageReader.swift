import Foundation

/// Any other web link (Chrome and most apps' Share buttons send only the link): the page is
/// loaded on the phone and read with the same page script Safari runs.
struct WebPageReader: SourceReader {
    let name = "web-page"
    /// RetAInPage.js; tests pass it in (the app bundle lacks it — only the extensions ship it).
    var script: String? = Bundle.main.url(forResource: "RetAInPage", withExtension: "js")
        .flatMap { try? String(contentsOf: $0, encoding: .utf8) }
    /// Ready once there's a page's worth of text — a script check page has almost none.
    static let ready = "document.readyState === 'complete' && document.body && document.body.innerText.split(/\\s+/).length > 100"

    func claims(_ input: ShareInput) -> Bool { input.webURL != nil }
    func read(_ input: ShareInput) async -> ReaderResult {
        guard let url = input.webURL, let page = await PageLoader.open(url, until: Self.ready) else { return Unusable.pageUnreadable }
        return await extract(from: page, url: input.url)
    }
    @MainActor func extract(from page: PageLoader, url: String?) async -> ReaderResult {
        guard let script, let json = await page.evaluate(script + """

            ;var out = null; ExtensionPreprocessingJS.run({completionFunction: function (r) { out = r; }});
            JSON.stringify(out)
            """) as? String,
              let res = try? JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: Any],
              let text = res["text"] as? String, Words.count(text) >= Words.min else { return Unusable.pageUnreadable }
        return .text(ShareRead(pageScript: res, text: text, url: url, extractor: "web-" + (res["extractor"] as? String ?? "none")))
    }
}
