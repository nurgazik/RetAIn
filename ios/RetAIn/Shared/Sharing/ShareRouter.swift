import Foundation

/// What the share sheet should do with a share.
enum ShareResult {
    case capture(String)
    case read(ShareRead, reader: String)
    case unusable(title: String, detail: String, reader: String)
}

/// Picks the reader for a share: readers are asked in order, the first to claim it reads it.
/// A new source is one new reader and one line in `readers`.
@MainActor
struct ShareRouter {
    var readers: [SourceReader] = [
        SelectionReader(),    // the user's own selection always wins
        SafariPageReader(),   // Safari ran our page script
        PlainTextReader(),    // text shared from any app
        RedditReader(),       // reddit links: the post, or the comment the link points to
        FacebookReader(),     // facebook links: public posts; private groups and logins explained
        WebPageReader(),      // any other web link (Chrome, other apps' Share buttons)
    ]

    func route(_ input: ShareInput) async -> ShareResult {
        if let word = input.singleWord { return .capture(word) }
        let reader = readers.first { $0.claims(input) }
        let name = reader?.name ?? "none"
        let words = Words.count(input.text)
        switch await reader?.read(input) ?? (words > 0 ? Unusable.tooShort(words) : Unusable.nothingToRead) {
        case .text(let read): return .read(read, reader: name)
        case .unusable(let t, let d): return .unusable(title: t, detail: d, reader: name)
        }
    }
}
