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

    /// The widget's line and the list's subtitle: the card's first meaning, else the stored one.
    var firstDefinition: String { card?.senses.first?.gloss ?? definition }
    var isUnverified: Bool { unverified ?? false }
}

/// A word card (D48): meanings in Wiktionary's order, examples written by the model.
struct Card: Codable, Hashable {
    let headword: String
    let source: String            // wiktionary | model
    let ipa: [Pronunciation]
    let sourceUrl: String?
    let senses: [Sense]
    struct Pronunciation: Codable, Hashable { let ipa: String; let tags: [String] }
    struct Sense: Codable, Hashable { let pos: String?; let gloss: String; let tags: [String]; let examples: [String] }
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
