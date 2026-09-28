import Foundation

/// The one-word capture rule, shared by the share sheet and Siri (AddWordIntent).
enum WordInput {
    /// A single word, lowercased, without surrounding punctuation ("Bolster." → "bolster"); nil otherwise.
    static func normalize(_ text: String?) -> String? {
        guard let t = text?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty,
              t.count <= 40, !t.contains(" ") else { return nil }
        let w = t.lowercased().trimmingCharacters(in: .punctuationCharacters)
        return w.isEmpty ? nil : w
    }
}
