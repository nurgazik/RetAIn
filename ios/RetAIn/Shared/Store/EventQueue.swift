import Foundation

/// What the phone reports for streaks and stats (D74): reader taps, piece opens, and words shown.
/// Each event gets its own id and the time it happened, waits as one small file in the app group (so the
/// app and the share/Safari extensions can all add to it without editing a shared file: Apple TN2408's
/// atomic-write advice), and is sent in batches. The server ignores an id it has seen, so a resend never
/// counts twice; anything it answers for (kept, resent or rejected) is done and leaves the queue.
actor EventQueue {
    static let shared = EventQueue()

    struct Event: Codable, Equatable {
        let id: String
        let kind: String         // tap | open | shown
        let surface: String      // reader | practice
        let at: String           // ISO 8601 with zone
        var pieceId: String?
        var word: String?
        var exercise: String?    // fill | write | hangman
        var wordId: Int?
        enum CodingKeys: String, CodingKey {
            case id, kind, surface, at, word, exercise
            case pieceId = "piece_id", wordId = "word_id"
        }
    }

    static let batch = 200
    static let maxAge: TimeInterval = 3 * 86_400   // the server drops events older than 3 days

    private let dir: URL
    private let send: ([Event]) async throws -> Void
    private var flushing = false
    private var scheduled: Task<Void, Never>?

    init(dir: URL? = nil, send: (([Event]) async throws -> Void)? = nil) {
        self.dir = dir ?? (FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: SessionStore.appGroup)
                           ?? FileManager.default.temporaryDirectory).appending(path: "events")
        self.send = send ?? { try await RetAInClient.shared.postEvents($0) }
        try? FileManager.default.createDirectory(at: self.dir, withIntermediateDirectories: true)
    }

    // MARK: what the screens call

    nonisolated func tap(pieceId: String, word: String) {
        Task { await add(.init(id: Self.newId(), kind: "tap", surface: "reader", at: Self.now(), pieceId: pieceId, word: word)) }
    }
    nonisolated func opened(pieceId: String) {
        Task { await add(.init(id: Self.newId(), kind: "open", surface: "reader", at: Self.now(), pieceId: pieceId)) }
    }
    nonisolated func shownInReader(pieceId: String, word: String) {
        Task { await add(.init(id: Self.newId(), kind: "shown", surface: "reader", at: Self.now(), pieceId: pieceId, word: word)) }
    }
    nonisolated func shownInPractice(exercise: String, wordId: Int) {
        Task { await add(.init(id: Self.newId(), kind: "shown", surface: "practice", at: Self.now(), exercise: exercise, wordId: wordId)) }
    }

    // MARK: the queue

    /// One file per event, written atomically; a send follows shortly (events come in bursts while reading).
    func add(_ e: Event) {
        guard let data = try? JSONEncoder().encode(e) else { return }
        try? data.write(to: dir.appending(path: "\(e.id).json"), options: .atomic)
        scheduled?.cancel()
        scheduled = Task { [weak self] in
            try? await Task.sleep(for: .seconds(2))
            guard !Task.isCancelled else { return }
            await self?.flush()
        }
    }

    /// Everything waiting, oldest first; files from more than 3 days ago are dropped (the server would too).
    func pending() -> [(url: URL, event: Event)] {
        let files = (try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)) ?? []
        let cutoff = Date().addingTimeInterval(-Self.maxAge)
        var out: [(URL, Event)] = []
        for f in files where f.pathExtension == "json" {
            guard let d = try? Data(contentsOf: f), let e = try? JSONDecoder().decode(Event.self, from: d),
                  let at = Self.parse(e.at), at > cutoff else { try? FileManager.default.removeItem(at: f); continue }
            out.append((f, e))
        }
        return out.sorted { $0.1.at < $1.1.at }
    }

    /// Send what's waiting in batches. A network failure keeps the rest for next time (the app sends again
    /// whenever it comes to the front); a batch the server refuses outright is dropped so it can't block the queue.
    func flush() async {
        guard !flushing else { return }
        flushing = true; defer { flushing = false }
        var waiting = pending()
        while !waiting.isEmpty {
            let chunk = Array(waiting.prefix(Self.batch))
            do {
                try await send(chunk.map(\.event))
            } catch APIError.http(let code, _) where (400..<500).contains(code) && code != 401 {
                // malformed for this server: drop it rather than retry forever
            } catch {
                return
            }
            chunk.forEach { try? FileManager.default.removeItem(at: $0.url) }
            waiting.removeFirst(chunk.count)
        }
    }

    // MARK: helpers

    nonisolated static func newId() -> String { UUID().uuidString.lowercased() }
    nonisolated static func now() -> String { stamp.string(from: Date()) }
    nonisolated static func parse(_ s: String) -> Date? { stamp.date(from: s) }
    private static let stamp: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
}
