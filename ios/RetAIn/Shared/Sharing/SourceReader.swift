import Foundation

/// One way of turning a share into reading text — one per source (Safari page, Reddit, any
/// web link…), so each source's quirks live in one file. `ShareRouter` asks the readers in
/// order; the first to claim a share reads it.
protocol SourceReader {
    /// Short name for diagnostics ("reddit", "web-page", …): success rates per source.
    var name: String { get }
    /// Is this share mine? Cheap and synchronous: no loading here.
    func claims(_ input: ShareInput) -> Bool
    @MainActor func read(_ input: ShareInput) async -> ReaderResult
}

enum ReaderResult {
    case text(ShareRead)
    /// Nothing usable; told to the reader in the source's own terms.
    case unusable(title: String, detail: String)
}

/// Text ready for the transform sheet, plus what the reader's header shows.
struct ShareRead {
    var text: String
    var title: String?
    var url: String?
    /// For the reader's header, never the model: request field → value (byline, site_name,
    /// published, dek), empty values left out.
    var sourceFields: [String: String] = [:]
    var extractor: String
    /// Shown above the piece in the share sheet: what the reader couldn't get and how to get it.
    var notice: String? = nil

    /// From RetAInPage.js's result dict (Safari's pre-step, or a page loaded on the phone).
    init(pageScript res: [String: Any], text: String, url: String?, extractor: String) {
        self.text = text
        self.title = res["title"] as? String
        self.url = url
        self.extractor = extractor
        for (key, field) in [("byline", "byline"), ("siteName", "site_name"),
                             ("publishedTime", "published"), ("dek", "dek")] {
            if let v = res[key] as? String, !v.isEmpty { sourceFields[field] = v }
        }
    }
    init(text: String, title: String? = nil, url: String? = nil, sourceFields: [String: String] = [:], extractor: String,
         notice: String? = nil) {
        self.text = text; self.title = title; self.url = url; self.sourceFields = sourceFields; self.extractor = extractor
        self.notice = notice
    }
}

enum Words {
    /// The engine needs about this many words to place any.
    static let min = 25
    static func count(_ s: String?) -> Int { s?.split(whereSeparator: { $0.isWhitespace }).count ?? 0 }
}

/// Messages more than one reader uses.
enum Unusable {
    static func tooShort(_ words: Int) -> ReaderResult {
        .unusable(title: "A little more, please",
                  detail: "That's \(words) word\(words == 1 ? "" : "s"); RetAIn needs about \(Words.min) to work with. Select a bit more and share again.")
    }
    static let nothingToRead = ReaderResult.unusable(
        title: "Nothing to read here",
        detail: "Select some text (about \(Words.min) words or more) and share the selection, or share a single word to capture it.")
    static let pageUnreadable = ReaderResult.unusable(
        title: "Couldn't read this page",
        detail: "It may need a login or a subscription. Select the text you're reading and share the selection instead.")
}
