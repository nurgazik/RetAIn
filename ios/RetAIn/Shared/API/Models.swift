import Foundation

struct Me: Codable { let userId: String; let email: String?; let learningWords: Int; let pieces: Int; let spendTodayUsd: Double?; let spendMonthUsd: Double? }
struct AuthResponse: Codable { let token: String; let userId: String; let newUser: Bool }

struct Word: Codable, Identifiable, Hashable {
    let id: Int
    let word: String
    let pos: String?
    let definition: String
    var status: String
    let added: String
    var servings: Int?
    // D48: the shared word card, and whether the word was found anywhere. Optional so the
    // widget's cached words.json from older builds still decodes.
    var card: Card? = nil
    var unverified: Bool? = nil
    /// The user's own note (D59): a translation, an example, anything. Never sent to a model.
    var note: String? = nil

    /// The widget's line and the list's subtitle: the card's first meaning, else the stored one.
    var firstDefinition: String { card?.senses.first?.gloss ?? definition }
    var rarity: Rarity? { card?.rarity }
    var isUnverified: Bool { unverified ?? false }
}

/// A word card (D48): meanings in Wiktionary's order, examples written by the model.
struct Card: Codable, Hashable {
    let headword: String
    let source: String            // wiktionary | model
    let ipa: [Pronunciation]
    let sourceUrl: String?
    let senses: [Sense]
    var rarity: Rarity? = nil     // D61; nil on cards cached before it
    struct Pronunciation: Codable, Hashable { let ipa: String; let tags: [String] }
    struct Sense: Codable, Hashable { let pos: String?; let gloss: String; let tags: [String]; let examples: [String] }
}

/// How common a word is (D61): wordfreq's Zipf score of the word family (src/service/rarity.py),
/// in five bands. More filled dots = more common, as in Collins' frequency bands.
struct Rarity: Codable, Hashable {
    let zipf: Double
    let band: String              // common | advanced | uncommon | rare | very-rare

    private var info: (label: String, level: Int, often: String) {
        switch band {
        case "common": ("Common", 5, "about once a book or more")
        case "advanced": ("Advanced", 4, "about once every 1–10 books")
        case "uncommon": ("Uncommon", 3, "about once every 10–100 books")
        case "rare": ("Rare", 2, "about once every 100–1,000 books")
        default: ("Very rare", 1, "less than once in 1,000 books")
        }
    }
    var label: String { info.label }
    /// "You'd meet it …", on an ~90,000-word book.
    var often: String { info.often }
    var dots: String { String(repeating: "●", count: info.level) + String(repeating: "○", count: 5 - info.level) }
}

struct Piece: Codable, Identifiable, Hashable {
    let id: String
    let createdAt: String
    let source: String?
    let title: String?
    let url: String?
    let bodyHtml: String?
    let attrib: String?
    // page metadata for the header (Safari shares); nil for other shares and older reads
    var byline: String? = nil
    var siteName: String? = nil
    var published: String? = nil
    var dek: String? = nil
    let offeredWords: [String]?
    let wordsUsed: [String]?
    let status: String
    let error: String?
    let latencyMs: Int?
    let costUsd: Double?
    var markCount: Int { (bodyHtml ?? "").components(separatedBy: "<mark").count - 1 }
}

struct PieceSummary: Codable, Identifiable, Hashable {
    let id: String
    let createdAt: String
    let source: String?
    let title: String?
    let url: String?
    let wordsUsed: [String]
    let status: String
    let latencyMs: Int?
    let costUsd: Double?
}

struct TransformAccepted: Codable { let pieceId: String; let eventsUrl: String }

enum TransformEvent { case phase(String), piece(Piece), error(String) }

enum APIError: LocalizedError {
    case http(Int, String), noSession, decode(String)
    var errorDescription: String? {
        switch self {
        case .http(let c, let m): return "Server said \(c): \(m)"
        case .noSession: return "Not signed in"
        case .decode(let m): return "Bad response: \(m)"
        }
    }
}

/// retain://word/<id> — the widget's tap target (the chevron still advances; UX-14).
enum WordLink {
    static func url(_ id: Int) -> URL { URL(string: "retain://word/\(id)")! }
    static func id(from url: URL) -> Int? {
        guard url.scheme == "retain", url.host() == "word" else { return nil }
        return Int(url.lastPathComponent)
    }
}

// MARK: daily practice (D56) — src/service/practice.py is the contract
struct PracticeSet: Codable {
    let day: String
    var items: [PracticeItem]
    /// Words of the list not yet in a round (D66: one list; the server splits the count by due / not due).
    var remaining: [String: Int]? = nil

    var left: Int { remaining?.values.reduce(0, +) ?? 0 }
    /// Words practised today (either exercise, or retained) / every learning word in the list.
    var wordProgress: (done: Int, total: Int) { (items.filter(\.practised).count, items.count + left) }
    var isDone: Bool { let p = wordProgress; return p.done == p.total }
    /// Words in today's rounds still untouched that have no fill-in sentence (the checks rejected them all).
    var withoutFill: [PracticeItem] { items.filter { $0.fill == nil && !$0.practised } }
}
struct PracticeItem: Codable, Identifiable, Hashable {
    let wordId: Int
    let word: String
    let definition: String
    let box: Int
    var fill: Fill?
    var attempts: Attempts
    var status: String
    var note: String? = nil   // the user's own note (D59), read live from the word
    var part: String? = nil   // today | ahead: due when it joined or not (the server's schedule rule, D66)
    var id: Int { wordId }
    var practised: Bool { attempts.fill != nil || attempts.write != nil || attempts.hangman != nil || status == "retained" }
    struct Fill: Codable, Hashable {
        let text: String; let source: String; let answer: String?
        var letters: Int? = nil     // the answer's length, for the gap's letter slots (D65); the word stays hidden
        var hint: [String]? = nil   // the Hint's options once asked for (D58): the word + lookalikes
        var wrong: [Wrong]? = nil   // today's wrong tries, each with its own meaning (tap to see)
    }
    struct Wrong: Codable, Hashable, Identifiable { let answer: String; let meaning: String?; var id: String { answer } }
    struct Attempts: Codable, Hashable { var fill: Attempt?; var write: Attempt?; var hangman: Attempt? = nil }
    struct Attempt: Codable, Hashable {
        let correct: Int?; let verdict: String?; let reason: String?; let fix: String?; let answer: String?
    }
}
/// A finished hangman game as the server re-checked it (D69).
struct HangmanResult: Codable, Hashable { let won: Bool; let wrong: Int; let word: String }
/// Right: expected (+ note when another form was typed). Wrong: the answer and its meaning; the word stays hidden (D58).
struct FillResult: Codable, Hashable {
    let correct: Bool; let expected: String?; let note: String?; let answer: String?; let meaning: String?
}
struct HintResult: Codable, Hashable { let options: [String] }
struct WriteResult: Codable, Hashable { let verdict: String; let reason: String?; let fix: String? }
