import Foundation

/// A Safari page: our page script (Readability) already ran in the user's own browser session,
/// so paywalled and logged-in pages work here.
struct SafariPageReader: SourceReader {
    let name = "safari-page"
    func claims(_ input: ShareInput) -> Bool { input.pageScript != nil }
    func read(_ input: ShareInput) async -> ReaderResult {
        let res = input.pageScript ?? [:], text = res["text"] as? String ?? ""
        guard Words.count(text) >= Words.min else { return Unusable.tooShort(Words.count(text)) }
        return .text(ShareRead(pageScript: res, text: text, url: input.url, extractor: res["extractor"] as? String ?? "none"))
    }
}
