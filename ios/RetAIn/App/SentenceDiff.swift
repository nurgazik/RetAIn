import SwiftUI

/// What the sentence check changed in the user's sentence (2026-11-16): the user's words vs the model's
/// "Polished:" / "Try:" version, compared word by word with punctuation as its own piece (Myers diff, Swift's
/// `difference(from:)`), so a missing comma or "the" shows as one small mark. Worked out on the phone: no
/// model step, no wait.
enum SentenceDiff {
    enum Kind: Equatable { case same, added, removed }
    struct Piece: Equatable {
        let text: String     // with the whitespace before it
        let kind: Kind
    }

    /// The fixed sentence in reading order, with removed pieces of the user's sentence before what replaced
    /// them. nil when most of the sentence changed: marks everywhere would just be noise.
    static func pieces(from mine: String, to fixed: String) -> [Piece]? {
        let a = tokens(mine), b = tokens(fixed)
        guard !b.isEmpty else { return nil }
        let diff = b.map(\.core).difference(from: a.map(\.core))
        var removed = Set<Int>(), added = Set<Int>()
        for change in diff {
            switch change {
            case .remove(let i, _, _): removed.insert(i)
            case .insert(let j, _, _): added.insert(j)
            }
        }
        guard (b.count - added.count) * 2 >= b.count else { return nil }   // under half kept: a rewrite
        var out: [Piece] = [], i = 0, j = 0
        while i < a.count || j < b.count {
            if i < a.count, removed.contains(i) {
                out.append(.init(text: a[i].text, kind: .removed)); i += 1
            } else if j < b.count, added.contains(j) {
                out.append(.init(text: b[j].text, kind: .added)); j += 1
            } else {
                if j < b.count { out.append(.init(text: b[j].text, kind: .same)) }
                i += 1; j += 1
            }
        }
        return out
    }

    /// Words (with apostrophes and hyphens inside) and single punctuation marks, each with the space before it.
    private static func tokens(_ s: String) -> [(text: String, core: String)] {
        let words = /\s*([\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*|[^\s\p{L}\p{N}])/
        return s.trimmingCharacters(in: .whitespacesAndNewlines).matches(of: words).map { m in
            let core = String(m.output.1)
            let space = m.output.0.first?.isWhitespace == true ? " " : ""   // runs of spaces count as one
            return (space + core, core)
        }
    }
}

/// The fixed sentence with what changed marked: added in highlighter, removed struck through in faint red.
struct MarkedFix: View {
    let mine: String
    let fixed: String

    var body: some View {
        Text(marked).font(.system(.callout, design: .serif)).fontDesign(.serif)
            .accessibilityLabel(fixed)   // VoiceOver reads the fixed sentence, not the marks
    }

    private var marked: AttributedString {
        guard let pieces = SentenceDiff.pieces(from: mine, to: fixed) else { return AttributedString(fixed) }
        return pieces.reduce(into: AttributedString()) { out, p in
            let lead = p.text.prefix { $0 == " " }, core = String(p.text.drop { $0 == " " })
            out += AttributedString(String(lead))
            switch p.kind {
            case .same:
                out += AttributedString(core)
            case .added:   // a lone comma gets hair spaces inside its highlight so it can be seen
                var s = AttributedString(core.count == 1 && !core.first!.isLetter ? "\u{200A}\(core)\u{200A}" : core)
                s.backgroundColor = .highlighter
                s.foregroundColor = .black   // dark ink on the highlighter in dark mode too
                out += s
            case .removed:
                var s = AttributedString(core)
                s.strikethroughStyle = .single
                s.foregroundColor = .red.opacity(0.6)
                out += s
            }
        }
    }
}
