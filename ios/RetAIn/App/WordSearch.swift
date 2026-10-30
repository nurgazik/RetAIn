import Foundation

/// Keyword search over the user's words, on the phone (the list is already loaded). Matching ignores
/// case, accents and extra spaces; with several terms, every term must match somewhere in the word.
/// Ranked: exact word, word starts with it, an inflection of the word ("bolstered" → bolster), word
/// contains it, the user's note (any language), a meaning, then near-misspellings of the word.
enum WordSearch {
    enum Field { case word, note, meaning }

    struct Hit: Identifiable {
        let word: Word
        let tier: Int          // lower = better (see `rank`)
        let field: Field       // where the best match is, for the row's second line
        let snippet: String?   // the matching note or meaning, when that's the reason
        var id: Int { word.id }
    }

    static func fold(_ s: String) -> String {
        s.folding(options: [.caseInsensitive, .diacriticInsensitive, .widthInsensitive], locale: .current)
            .split(whereSeparator: \.isWhitespace).joined(separator: " ")
    }

    static func results(_ words: [Word], _ query: String) -> [Hit] {
        let q = fold(query)
        guard !q.isEmpty else { return [] }
        let terms = q.split(separator: " ").map(String.init)
        return words.compactMap { hit($0, q, terms) }
            .sorted { ($0.tier, $0.word.word.count, $0.word.word) < ($1.tier, $1.word.word.count, $1.word.word) }
    }

    /// Whether `query` names a word already in the list (then search offers no "Add").
    static func hasExact(_ words: [Word], _ query: String) -> Bool {
        let q = fold(query)
        return words.contains { fold($0.word) == q }
    }

    private static func hit(_ w: Word, _ q: String, _ terms: [String]) -> Hit? {
        let word = fold(w.word)
        if word == q { return Hit(word: w, tier: 0, field: .word, snippet: nil) }
        if word.hasPrefix(q) { return Hit(word: w, tier: 1, field: .word, snippet: nil) }
        if inflection(of: word, q) { return Hit(word: w, tier: 2, field: .word, snippet: nil) }
        if word.contains(q) { return Hit(word: w, tier: 3, field: .word, snippet: nil) }
        let note = fold(w.note ?? "")
        let meanings = (w.card?.senses.map(\.gloss) ?? []) + (w.definition.isEmpty ? [] : [w.definition])
        let folded = meanings.map(fold)
        let everywhere = ([word, note] + folded).joined(separator: "\n")
        if terms.allSatisfy({ everywhere.contains($0) }) {  // every term somewhere: say where the best one is
            if terms.contains(where: { note.contains($0) }) { return Hit(word: w, tier: 4, field: .note, snippet: w.note) }
            if let i = folded.firstIndex(where: { m in terms.contains { m.contains($0) } }) {
                return Hit(word: w, tier: 5, field: .meaning, snippet: meanings[i])
            }
            return Hit(word: w, tier: 3, field: .word, snippet: nil)
        }
        return nearMiss(word, q) ? Hit(word: w, tier: 6, field: .word, snippet: nil) : nil
    }

    /// The query looks like an inflected form of the word: bolstered, bolsters → bolster;
    /// exigencies → exigency; stoking → stoke; stopped → stop. Inflectional endings only, so
    /// "gazette" doesn't count as a form of "gaze".
    static func inflection(of word: String, _ q: String) -> Bool {
        guard word.count >= 4, q != word, !q.contains(" ") else { return false }
        let stem = word.hasSuffix("e") || word.hasSuffix("y") ? String(word.dropLast()) : word
        guard q.hasPrefix(stem) else { return false }
        let rest = String(q.dropFirst(stem.count))
        let endings = ["s", "es", "d", "ed", "ing", "er", "est", "ies", "ied", "ier", "iest"]
        return endings.contains(rest) || (rest.first == word.last && endings.contains(String(rest.dropFirst())))
    }

    /// A likely misspelling of the word: one letter off for short words, two for long ones.
    static func nearMiss(_ word: String, _ q: String) -> Bool {
        guard q.count >= 4, !q.contains(" "), abs(word.count - q.count) <= 2 else { return false }
        return editDistance(word, q) <= (q.count >= 8 ? 2 : 1)
    }

    /// Levenshtein distance: single-letter inserts, deletes and substitutions.
    static func editDistance(_ a: String, _ b: String) -> Int {
        let a = Array(a), b = Array(b)
        var row = Array(0...b.count)
        for i in 1...max(a.count, 1) where !a.isEmpty {
            var prev = row[0]; row[0] = i
            for j in 1...max(b.count, 1) where !b.isEmpty {
                let cur = row[j]
                row[j] = min(row[j] + 1, row[j - 1] + 1, prev + (a[i - 1] == b[j - 1] ? 0 : 1))
                prev = cur
            }
        }
        return a.isEmpty ? b.count : row[b.count]
    }
}
