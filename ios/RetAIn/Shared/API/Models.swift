import Foundation

struct Me: Codable { let userId: String; let email: String?; let learningWords: Int; let pieces: Int }
struct AuthResponse: Codable { let token: String; let userId: String; let newUser: Bool }

struct Word: Codable, Identifiable, Hashable {
    let id: Int
    let word: String
    let pos: String?
    let definition: String
    var status: String
    let added: String
    var servings: Int?
}

struct Piece: Codable, Identifiable, Hashable {
    let id: String
    let createdAt: String
    let source: String?
    let title: String?
    let url: String?
    let bodyHtml: String?
    let attrib: String?
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
