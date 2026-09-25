import Foundation

/// App-group container shared by the app and both extensions (G1 sub-question e).
enum SharedStore {
    static let group = "group.com.retain.spike"
    static var containerURL: URL? { FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: group) }
    static var available: Bool { containerURL != nil }
    private static var file: URL { (containerURL ?? FileManager.default.temporaryDirectory).appending(path: "reads.json") }

    static func load() -> [Piece] {
        guard let d = try? Data(contentsOf: file) else { return [] }
        return (try? JSONDecoder().decode([Piece].self, from: d)) ?? []
    }
    static func save(_ p: Piece) {
        var all = load()
        all.removeAll { $0.id == p.id }
        all.insert(p, at: 0)
        try? JSONEncoder().encode(all).write(to: file, options: .atomic)
    }
    /// Debug log shared with the app so extension findings can be read without a debugger.
    static func log(_ line: String) {
        let url = (containerURL ?? FileManager.default.temporaryDirectory).appending(path: "spike.log")
        let stamp = ISO8601DateFormatter().string(from: Date())
        let data = "\(stamp) \(line)\n".data(using: .utf8)!
        if let h = try? FileHandle(forWritingTo: url) { h.seekToEndOfFile(); h.write(data); try? h.close() }
        else { try? data.write(to: url) }
    }
    static func readLog() -> String {
        let url = (containerURL ?? FileManager.default.temporaryDirectory).appending(path: "spike.log")
        return (try? String(contentsOf: url, encoding: .utf8)) ?? "(no log yet)"
    }
}
